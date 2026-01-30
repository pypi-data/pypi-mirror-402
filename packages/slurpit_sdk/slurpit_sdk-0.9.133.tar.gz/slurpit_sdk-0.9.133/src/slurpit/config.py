"""
Global configuration settings for the Slurpit SDK.
"""

class Config:
    """Global configuration class for Slurpit SDK settings."""
    
    def __init__(self):
        self.auto_pagination = True
    
    def set_auto_pagination(self, enabled: bool):
        """Set the global auto-pagination setting."""
        self.auto_pagination = enabled
    
    def get_auto_pagination(self) -> bool:
        """Get the current auto-pagination setting."""
        return self.auto_pagination

# Global instance
config = Config() 