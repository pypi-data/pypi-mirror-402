"""Interactive Shell for Tortoise ORM."""
import asyncio
import sys
from pathlib import Path

from tortoise import Tortoise
from loguru import logger

from .database import TORTOISE_ORM


async def init_tortoise():
    """Initialize Tortoise ORM for shell."""
    await Tortoise.init(config=TORTOISE_ORM)
    logger.info("Tortoise ORM initialized for shell")


async def close_tortoise():
    """Close Tortoise ORM connections."""
    await Tortoise.close_connections()


async def run_shell(shell_command=None):
    """Run interactive shell with Tortoise ORM models available."""
    await init_tortoise()
    
    try:
        # Import models for convenience
        from .models import Workspace, PublishRecord, Setting
        from tortoise.models import Model
        from tortoise import fields
        
        models_intro = """
Available models:
- Workspace: Workspace management
- PublishRecord: Publishing records
- Setting: Application settings

Example queries:
- workspaces = await Workspace.all()
- records = await PublishRecord.filter(status='published').all()
- await Workspace.create(name='Test', folder_path='/path/to/folder')
"""
        
        print("=" * 60)
        print("Markdown to Blog - Tortoise ORM Interactive Shell")
        print("=" * 60)
        print(models_intro)
        print("-" * 60)
        print("Tip: Use 'exit()' or 'quit()' to exit the shell")
        print("-" * 60)
        print()
        
        # Setup namespace
        namespace = {
            '__name__': '__main__',
            '__doc__': None,
            'Workspace': Workspace,
            'PublishRecord': PublishRecord,
            'Setting': Setting,
            'Tortoise': Tortoise,
            'Model': Model,
            'fields': fields,
            'asyncio': asyncio,
        }
        
        # Execute single command if provided
        if shell_command:
            # Run the shell_command through the event loop
            compiled_code = compile(shell_command, "<string>", "single")
            eval(compiled_code, namespace)
        else:
            # Interactive shell
            import code as code_module
            
            # Start interactive shell
            try:
                import IPython
                from IPython.terminal.embed import InteractiveShellEmbed
                
                # Embed IPython shell
                shell = InteractiveShellEmbed()
                shell.push(namespace)
                shell.show_banner = False
                shell()
            except ImportError:
                # Fallback to standard code.interact if IPython not available
                code_module.interact(banner="", local=namespace)
            
    finally:
        await close_tortoise()

