# Аврора / Aurora  v0

Личный офлайн-спутник для ПК. Текстовый чат. Свой язык **LC**. Без облака.

**Никаких Llama, Ollama, OpenAI, Anthropic, Gemini, xAI и прочих облачных мозгов.**  
Аврора отвечает только из файлов на диске: `brain/*.avr` + `persona/` + `memory/`.

Скрытый рантайм — Python. Для тебя она не «питоновский бот», а **Аврора**, и думает она на LC.

> `(LC. 31. print(null));` — пауза. Пустой выдох. Ничего не печатает.

---

## Windows: как запустить

1. Установи [Python 3.10+](https://www.python.org/downloads/) (галочка **Add python.exe to PATH**).
2. Tkinter уже в официальном установщике Windows — отдельно ничего ставить не нужно. **pip не обязателен.**
3. Скачай или клонируй этот репозиторий.
4. В проводнике зайди в папку Авроры. В адресной строке набери `cmd` и Enter.

```bat
py -3 -m aurora
```

Если `py` не находится:

```bat
python -m aurora
```

Или дважды кликни `run.bat`.

Окно чата — тёмное, офлайн. Пишешь текст → Аврора отвечает. Голоса в v0 нет.

Терминал без окна:

```bat
py -3 -m aurora --cli
py -3 -m aurora --once "привет"
```

Проверка парсера LC:

```bat
py -3 -m unittest discover -s tests -v
```

Linux / macOS: то же самое, `python3 -m aurora` (нужен пакет tkinter: `python3-tk`).

---

## Где она живёт

| путь | смысл |
|---|---|
| `brain/*.avr` | мысли на LC |
| `persona/persona.md` | голос, «ты», кто она |
| `memory/me.md` | досье; сейчас имя **Артём** — правь файл |
| `memory/notes.md` | то, что попросишь запомнить |
| `docs/AURORA_LC.md` | язык LC, RU+EN |

Напиши «привет», «кто ты», «как меня зовут», «меня зовут …», «запомни …», «что такое LC».

Персону и досье можно править в блокноте — после следующего сообщения Аврора перечитывает диск (boot: `load_persona` / `load_memory`).

---

## English (short)

Offline PC companion. Text chat only. Custom LC brain, no cloud LLMs, no Ollama/Llama. Run `py -3 -m aurora` on Windows. Persona uses informal «ты». User dossier placeholder name: Артём.
