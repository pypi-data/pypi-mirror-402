import sys
from pathlib import Path


def load_template(template_name: str, token: str):
    template_path = Path(__file__).parent / "templates" / template_name
    if not template_path.exists():
        print(f"❌ Шаблон '{template_name}' не найден!")
        sys.exit(1)
    
    template_file = template_path / "bot.py"
    if not template_file.exists():
        print(f"❌ Файл bot.py не найден в шаблоне '{template_name}'!")
        sys.exit(1)
    
    with open(template_file, 'r', encoding='utf-8') as f:
        code = f.read()
    
    code = code.replace('TOKEN = "YOUR_BOT_TOKEN"', f'TOKEN = "{token}"')
    
    exec_globals = {
        '__name__': '__main__',
        '__file__': str(template_file)
    }
    
    exec(compile(code, str(template_file), 'exec'), exec_globals)


def main():
    if len(sys.argv) < 3:
        print("Использование: bongram <template> <token>")
        print("Пример: bongram support YOUR_BOT_TOKEN")
        sys.exit(1)
    
    template_name = sys.argv[1]
    token = sys.argv[2]
    
    if not token or token == "YOUR_BOT_TOKEN":
        print("❌ Ошибка: Укажите токен бота!")
        sys.exit(1)
    
    load_template(template_name, token)
