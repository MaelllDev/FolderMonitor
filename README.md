# 📁 FolderMonitor

Aplicativo desktop Windows que monitora alterações em uma pasta em tempo real.
Ideal para acompanhar mudanças durante desenvolvimento de projetos e mods.

---

## ✨ Principais funcionalidades

- Monitoramento de arquivos baseado em eventos do sistema (Windows)
- Detecta arquivos **criados**, **excluídos**, **modificados** e **renomeados**
- Agrupa eventos por **extensão** quando ativado
- Ícone de bandeja com menu completo via `pystray`
- Notificações nativas do Windows
- Relatórios em texto exportáveis (`.txt`)
- Histórico de sessões salvo automaticamente
- Inicialização automática com o Windows (registro)
- Interface moderna com `customtkinter` e fallback para `tkinter`
- Baixo consumo de memória e CPU

---

## 📦 Estrutura do projeto

```
FolderMonitor/
├── main.py              ← ponto de entrada
├── app.py               ← orquestra o aplicativo
├── monitor.py           ← monitoramento de arquivos (watchdog)
├── tray_handler.py      ← ícone da bandeja e menu do system tray
├── reports.py           ← geração de relatórios e histórico
├── config_manager.py    ← persistência de configurações e dados
├── settings_win.py      ← janela de configurações
├── stats_win.py         ← janela de estatísticas em tempo real
├── icon_gen.py          ← geração de ícones com Pillow
├── generate_icon.py     ← script auxiliar para gerar `icon.ico`
├── main.spec            ← configuração do PyInstaller
├── build.bat            ← build automatizado do executável
└── requirements.txt     ← dependências Python
```

---

## 🚀 Instalação e uso

### Requisitos

- Windows 10 ou 11
- Python 3.11+

### Instalação rápida

```bash
cd FolderMonitor
pip install -r requirements.txt
python main.py
```

### Como usar

- O app inicia minimizado na bandeja do sistema.
- Clique com o botão direito no ícone para abrir o menu.
- `Ver Estatísticas`, `Configurações`, `Salvar Relatório`, `Pausar`, `Continuar`, `Fechar`, etc.

---

## 🏗️ Gerar executável (.exe)

### Opção recomendada

Execute:

```bash
build.bat
```

### Opção manual

```bash
python generate_icon.py
pyinstaller main.spec --noconfirm --clean
```

### Resultado

- Executável em `dist\FolderMonitor.exe`
- Ícone embutido a partir de `icon.ico`
- Sem janela de console (`console=False`)
- Compactado com `UPX` se disponível

---

## 📌 Dependências

- `watchdog>=4.0.0` — monitoramento de arquivos no Windows
- `pystray>=0.19.5` — tray icon e menu
- `Pillow>=10.0.0` — geração de ícones
- `customtkinter>=5.2.0` — interface opcional moderna
- `pyinstaller>=6.0.0` — empacotamento em .exe

> `customtkinter` é opcional; sem ele o app usa `tkinter` padrão.

---

## ⚙️ Configurações importantes

O app salva dados em `%APPDATA%\FolderMonitor`.

- `monitored_folder` — pasta observada
- `auto_start_monitoring` — iniciar monitorando ao abrir o app
- `start_with_windows` — iniciar com o Windows
- `save_report_on_exit` — gerar relatório ao fechar
- `notifications_enabled` — ativar notificações
- `track_by_extension` — agrupar por extensão
- `ignore_patterns` — padrões a ignorar
- `max_history_sessions` — limite de sessões salvas

---

## 🧠 Como o monitor funciona

- Usa `watchdog` com backend nativo do Windows.
- Processa eventos sem polling constante.
- Incrementa contadores de evento em tempo real.
- Filtra arquivos e pastas indesejados.
- Executa o observer em thread separada para manter a UI responsiva.

---

## 📄 Relatórios e histórico

- Relatórios salvos em `%APPDATA%\FolderMonitor\reports`
- Nome padrão: `relatorio_YYYYMMDD_HHMMSS.txt`
- Inclui data, pasta, duração, totais e resumo por extensão
- Histórico de sessões em `%APPDATA%\FolderMonitor\sessions.json`

---

## 🗂️ Arquivos gerados pelo app

| Arquivo                                      | Conteúdo                    |
|---------------------------------------------|-----------------------------|
| `%APPDATA%\FolderMonitor\config.json`     | Configurações do app        |
| `%APPDATA%\FolderMonitor\sessions.json`   | Histórico de sessões        |
| `%APPDATA%\FolderMonitor\reports\*.txt`  | Relatórios exportados       |
| `%APPDATA%\FolderMonitor\app.log`         | Log de execução do app      |

---

## 🐛 Solução de problemas

**Ícone não aparece na bandeja**
- Verifique se o antivírus não está bloqueando o app.
- Confirme se `pystray` e `Pillow` estão instalados.

**Janela de console no .exe**
- Recompile com `pyinstaller main.spec --noconfirm --clean`.
- Verifique se `console=False` está definido em `main.spec`.

**`customtkinter` não encontrado**
- Instale com `pip install customtkinter`.
- O app ainda funciona com `tkinter` padrão.

**Erro no PyInstaller**
- Instale `pyinstaller` e as dependências listadas.
- Ajuste `hiddenimports` em `main.spec` se precisar.

---

## 💡 Observações finais

- O projeto é voltado para Windows.
- O app mantém a interface leve e eficiente.
- Ajuste as configurações para seu fluxo de trabalho.
- Monitore apenas a pasta de trabalho ativa.

---

## 📄 Licença

MIT — livre para uso pessoal e comercial.
