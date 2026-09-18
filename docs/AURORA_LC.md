# Aurora LC / Язык Авроры

Коротко. RU, then EN.

Аврора думает не «промптом в облаке», а выражениями LC в файлах `brain/*.avr`.
Скрытый рантайм может быть Python — для тебя она Аврора, а мозг — LC.

---

## RU

### Форма

```
(LC. <id>. <вызов>);
```

Цепочка через точку:

```
(LC. 20. if_contains("привет", "hello").reply("Привет, {name}."));
```

Канонический пример:

```
(LC. 31. print(null));
```

`print(null)` — **пустой выдох**. Ничего не печатает и ничего не говорит. Это пауза между мыслями, не ошибка.

Комментарии: `// так` или `# так`. Строки — в `"..."` или `'...'`.

`id` — число или dotted (`31`, `20.1`). Файлы `brain/*.avr` читаются по имени, внутри — по id.

Первый сработавший `reply` / `greet` / `identity` в ходе ответа побеждает. Дальше можно ещё `remember`, но новый голос не перебивает.

Шаблоны: `{name}`, `{me}`, `{memory_sheet}`, `{remember_ack}`, `{user_message}` — из persona и memory.

### Команды (v0)

| Команда | Смысл |
|---|---|
| `print(null)` | молчание / пауза |
| `reply("текст")` | сказать пользователю |
| `greet()` | приветствие из `persona.md` |
| `identity()` | кто такая Аврора |
| `if_contains("a", "b")` | если в фразе есть одно из слов — дальше по цепочке |
| `match(...)` | то же, что `if_contains` |
| `load_persona()` | перечитать `persona/persona.md` |
| `load_memory()` | перечитать `memory/me.md` |
| `recall()` / `recall("name")` | поднять досье в шаблоны |
| `remember("key", "value")` | записать факт в `memory/me.md` |
| `remember_from_message()` | разобрать «меня зовут …» / «запомни …» |
| `note("текст")` | дописать в `memory/notes.md` |
| `fallback()` | только если ещё не ответила |
| `stop()` | оборвать мысль |

Нет сети. Нет Llama, Ollama, OpenAI, Anthropic, Gemini, xAI.

---

## EN

Aurora’s brain language. Statements look like dream-syntax:

```
(LC. 31. print(null));
```

`print(null)` is defined as **silence**: no user-visible output. A rest between thoughts.

Shape: `(LC. <id>. <call-chain>);`  
Calls may chain: `if_contains("hi").greet();`

Commands: `print`, `reply`, `greet`, `identity`, `if_contains` / `match`, `load_persona`, `load_memory`, `recall`, `remember`, `remember_from_message`, `note`, `fallback`, `stop`.

Replies are interpolated from `persona/` + `memory/` on disk. Nothing is fetched from a cloud LLM.
