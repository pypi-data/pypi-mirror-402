"""Template rendering for YAML deployment files."""

import yaml
from pathlib import Path
from typing import Dict, Any
from jinja2 import Template

from northserve.constants import CONFIGS_DIR, YAML_TEMPLATES_DIR
from northserve.models.deployment import EngineConfig
from northserve.utils.logger import get_logger

logger = get_logger(__name__)


class TemplateRendererError(Exception):
    """Exception raised for template rendering errors."""
    pass


class TemplateRenderer:
    """Handles Jinja2 template rendering for deployment YAMLs."""

    def __init__(self):
        """Initialize template renderer."""
        self.configs_dir = CONFIGS_DIR
        self.templates_dir = YAML_TEMPLATES_DIR

    def load_engine_config(self, config_path: Path) -> EngineConfig:
        """
        Load and validate engine configuration from YAML.

        Args:
            config_path: Path to engine config YAML file

        Returns:
            EngineConfig instance

        Raises:
            TemplateRendererError: If config is invalid
        """
        if not config_path.exists():
            raise TemplateRendererError(f"Config file not found: {config_path}")

        try:
            with open(config_path, 'r') as f:
                content = yaml.safe_load(f)

            # Validate required fields
            if 'image' not in content:
                raise TemplateRendererError(
                    f"Config {config_path} missing required field 'image'"
                )

            if 'cmd' not in content:
                raise TemplateRendererError(
                    f"Config {config_path} missing required field 'cmd'"
                )

            if not isinstance(content['cmd'], list):
                raise TemplateRendererError(
                    f"'cmd' in {config_path} must be a list"
                )

            return EngineConfig(
                image=content['image'],
                cmd=content['cmd'],
                liveness_path=content.get('livenessPath'),
                readiness_path=content.get('readinessPath')
            )

        except yaml.YAMLError as e:
            raise TemplateRendererError(f"Invalid YAML in {config_path}: {e}")

    def render_image_template(self, image_template: str, context: Dict[str, Any]) -> str:
        """
        Render image template if IMAGE_VERSION is specified.

        Args:
            image_template: Image template string
            context: Rendering context

        Returns:
            Rendered image string
        """
        if context.get('IMAGE_VERSION') is not None:
            template = Template(image_template)
            return template.render(**context)
        return image_template

    def add_engine_config_to_context(
        self,
        config_path: Path,
        context: Dict[str, Any],
        prefix: str = ''
    ) -> Dict[str, Any]:
        """
        Load engine config and add to rendering context.

        Args:
            config_path: Path to engine config file
            context: Existing rendering context
            prefix: Prefix for context keys (e.g., 'PREFILL_', 'DECODE_')

        Returns:
            Updated context dictionary
        """
        # Load engine config
        engine_config = self.load_engine_config(config_path)

        # Render image template if needed
        image = self.render_image_template(engine_config.image, context)

        # Determine context keys based on prefix
        image_key = f'{prefix}IMAGE' if prefix else 'IMAGE'
        cmdline_key = f'{prefix}CMDLINE' if prefix else 'CMDLINE'

        # Add image to context
        context[image_key] = image

        # Add liveness/readiness paths (only for normal mode, not prefixed)
        if not prefix:
            if engine_config.liveness_path:
                context['LIVENESS_PATH'] = engine_config.liveness_path
            if engine_config.readiness_path:
                context['READINESS_PATH'] = engine_config.readiness_path

        # Add API key to extra commands if specified (only for normal mode)
        if context.get('API_KEY') and not prefix:
            extra_cmds = context.get('EXTRA_CMDS', '')
            context['EXTRA_CMDS'] = f"{extra_cmds} --api-key {context['API_KEY']}".strip()

        # Build command line
        cmds = engine_config.cmd.copy()

        # Append EXTRA_CMDS for normal mode and PD mode (not minilb)
        if context.get('EXTRA_CMDS') and prefix != 'MINILB_':
            cmds.append(context['EXTRA_CMDS'])

        # Render command line template
        cmdline_template = Template(' '.join(cmds))
        context[cmdline_key] = cmdline_template.render(**context)

        # Special handling for multi-node worker commands
        if not context.get('USE_RAY_CLUSTER') and not prefix:
            context['MULTI_NODE_WORKER_INIT_CMDS'] = context['CMDLINE']

        return context

    def get_engine_config_path(
        self,
        backend: str,
        protocol: str,
        profile: str
    ) -> Path:
        """
        Get path to engine configuration file.

        Args:
            backend: Backend type (e.g., 'sglang', 'vllm')
            protocol: Protocol type (e.g., 'openai', 'anthropic')
            profile: Profile type (e.g., 'generation', 'sleep')

        Returns:
            Path to config file
        """
        filename = f"{backend}_{protocol}_{profile}.yaml"
        return self.configs_dir / filename

    def get_pd_config_paths(
        self,
        backend: str,
        protocol: str,
        template_name: str
    ) -> Dict[str, Path]:
        """
        Get paths to PD separation mode config files.

        Args:
            backend: Backend type
            protocol: Protocol type
            template_name: Name of the template file

        Returns:
            Dictionary with config paths for prefill, decode, and minilb
        """
        configs = {}

        if 'prefill' in template_name:
            configs['prefill'] = self.configs_dir / f"{backend}_{protocol}_pdpre.yaml"
        elif 'decode' in template_name:
            configs['decode'] = self.configs_dir / f"{backend}_{protocol}_pddec.yaml"
        elif 'minilb' in template_name:
            configs['minilb'] = self.configs_dir / f"{backend}_{protocol}_minilb.yaml"

        return configs

    def render_template(
        self,
        template_path: Path,
        context: Dict[str, Any]
    ) -> str:
        """
        Render a Jinja2 template with given context.

        Args:
            template_path: Path to template file
            context: Rendering context

        Returns:
            Rendered template string

        Raises:
            TemplateRendererError: If rendering fails
        """
        if not template_path.exists():
            raise TemplateRendererError(f"Template not found: {template_path}")

        try:
            with open(template_path, 'r') as f:
                template_content = f.read()

            template = Template(template_content)
            return template.render(**context)

        except Exception as e:
            raise TemplateRendererError(f"Failed to render template {template_path}: {e}")

    def save_rendered_template(
        self,
        rendered_content: str,
        output_path: Path
    ) -> None:
        """
        Save rendered template to file.

        Args:
            rendered_content: Rendered template content
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered_content)
        logger.debug(f"Saved rendered template to {output_path}")


