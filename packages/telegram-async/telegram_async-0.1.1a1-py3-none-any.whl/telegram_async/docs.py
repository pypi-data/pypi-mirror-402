from telegram_async.decorators import command

def generate_help(dispatcher) -> str:
    """
    Generuje tekst help z listą komend i minimalną info
    """
    lines = ["📖 Lista komend:"]
    for cmd, (handler, role) in dispatcher.command_handlers.items():
        lines.append(f"{cmd} - minimalna rola: {role.name}")
    return "\n".join(lines)

async def send_help(ctx, dispatcher):
    help_text = generate_help(dispatcher)
    await ctx.reply(help_text)
