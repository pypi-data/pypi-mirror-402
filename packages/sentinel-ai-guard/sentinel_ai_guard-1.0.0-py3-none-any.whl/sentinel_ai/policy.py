"""
Security Policy Management
==========================

Manages risk levels and tool permissions.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml


class SecurityPolicy:
    """
    Manages security policies for tool execution.
    
    Can load from YAML file or be configured programmatically.
    """
    
    DEFAULT_POLICY = {
        'version': '1.0.0',
        'security_levels': {
            'high': {
                'require_consensus': True,
                'allow_untrusted_data': False
            },
            'medium': {
                'require_consensus': False,
                'allow_untrusted_data': True
            },
            'low': {
                'require_consensus': False,
                'allow_untrusted_data': True
            }
        },
        'default_risk': 'medium'
    }
    
    def __init__(self, policy_path: Optional[str] = None, policy_dict: Optional[Dict] = None):
        """
        Initialize security policy.
        
        Args:
            policy_path: Path to YAML policy file (optional)
            policy_dict: Policy dictionary (optional, overrides file)
        """
        if policy_dict:
            self.policy = policy_dict
        elif policy_path:
            self.policy = self._load_from_file(policy_path)
        else:
            self.policy = self.DEFAULT_POLICY.copy()
        
        self.tools: Dict[str, Dict[str, Any]] = self.policy.get('tools', {})
    
    def _load_from_file(self, path: str) -> Dict:
        """Load policy from YAML file."""
        policy_file = Path(path)
        if not policy_file.exists():
            raise FileNotFoundError(f"Policy file not found: {path}")
        
        with open(policy_file, 'r') as f:
            return yaml.safe_load(f)
    
    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool configuration dictionary
        """
        return self.tools.get(tool_name, {
            'risk': self.policy.get('default_risk', 'medium')
        })
    
    def get_security_level(self, risk: str) -> Dict[str, Any]:
        """
        Get security level configuration.
        
        Args:
            risk: Risk level ('high', 'medium', 'low')
            
        Returns:
            Security level configuration
        """
        return self.policy['security_levels'].get(risk, {
            'require_consensus': False,
            'allow_untrusted_data': True
        })
    
    def register_tool(self, tool_name: str, risk: str = 'medium', description: str = ''):
        """
        Register a tool with the policy.
        
        Args:
            tool_name: Name of the tool
            risk: Risk level ('high', 'medium', 'low')
            description: Tool description
        """
        self.tools[tool_name] = {
            'risk': risk,
            'description': description
        }
    
    def set_tool_risk(self, tool_name: str, risk: str):
        """
        Update risk level for a tool.
        
        Args:
            tool_name: Name of the tool
            risk: New risk level
        """
        if tool_name in self.tools:
            self.tools[tool_name]['risk'] = risk
        else:
            self.register_tool(tool_name, risk)
