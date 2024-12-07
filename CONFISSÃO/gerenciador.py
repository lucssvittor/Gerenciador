
import PySimpleGUI as sg
from datetime import datetime
import json
import hashlib

# Arquivos para salvar os dados
USERS_FILE = "usuarios.json"
DATABASE_FILE = "pecados.json"

# Função para calcular o tempo desde o último pecado
def calcular_dias(data_str):
    try:
        data = datetime.strptime(data_str, "%d/%m/%Y")
        hoje = datetime.now()
        return (hoje - data).days
    except ValueError:
        return "Data inválida"

# Carregar dados do arquivo JSON
def carregar_dados(arquivo, vazio_padrao):
    try:
        with open(arquivo, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return vazio_padrao

# Salvar dados no arquivo JSON
def salvar_dados(arquivo, dados):
    with open(arquivo, "w") as file:
        json.dump(dados, file, indent=4)

# Função para criar hash de senha
def criar_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# Layout da tela de login
def tela_login():
    layout = [
        [sg.Text("Usuário"), sg.InputText(key='-USER-')],
        [sg.Text("Senha"), sg.InputText(key='-PASSWORD-', password_char="*")],
        [sg.Button("Entrar"), sg.Button("Criar Usuário"), sg.Button("Sair")]
    ]
    return sg.Window("Login", layout, finalize=True)

# Layout para criar usuário
def tela_criar_usuario():
    layout = [
        [sg.Text("Novo Usuário"), sg.InputText(key='-NEW_USER-')],
        [sg.Text("Nova Senha"), sg.InputText(key='-NEW_PASSWORD-', password_char="*")],
        [sg.Text("Confirmar Senha"), sg.InputText(key='-CONFIRM_PASSWORD-', password_char="*")],
        [sg.Button("Salvar Usuário"), sg.Button("Voltar")]
    ]
    return sg.Window("Criar Usuário", layout, finalize=True)

# Layout principal do programa
def tela_principal():
    layout = [
        [sg.Text("Pecado:"), sg.InputText(key='-PECADO-', size=(20, 1)), sg.Text("Data (dd/mm/aaaa):"), sg.InputText(key='-DATA-', size=(20, 1))],
        [sg.Button("Adicionar"), sg.Button("Atualizar Pecado"), sg.Button("Remover Pecado"), sg.Button("Visualizar Detalhes"), sg.Button("Sair")],
        [sg.Text("Lista de Pecados:")],
        [sg.Listbox(values=[], size=(70, 10), key='-LISTA-', enable_events=True)]
    ]
    return sg.Window("CONFISSÃO", layout, finalize=True)

# Variáveis iniciais
usuarios = carregar_dados(USERS_FILE, {})
pecados = carregar_dados(DATABASE_FILE, {})
login_window = tela_login()
main_window = None
create_user_window = None

# Atualizar lista na interface
def atualizar_lista(window):
    lista = []
    for pecado, info in pecados.items():
        dias = calcular_dias(info["data"])
        lista.append(f"Pecado: {pecado} - Dias sem cometer: {dias if isinstance(dias, int) else 'Desconhecido'}")
    window['-LISTA-'].update(lista)

# Loop principal
while True:
    window, event, values = sg.read_all_windows()

    # Fechar janela de login
    if event in (sg.WINDOW_CLOSED, "Sair") and window == login_window:
        break

    # Fechar janela de criação de usuário
    if event in (sg.WINDOW_CLOSED, "Voltar") and window == create_user_window:
        create_user_window.close()
        create_user_window = None

    # Login
    if event == "Entrar" and window == login_window:
        usuario = values['-USER-'].strip()
        senha = values['-PASSWORD-'].strip()
        senha_hash = criar_hash(senha)

        if usuario in usuarios and usuarios[usuario] == senha_hash:
            login_window.close()
            main_window = tela_principal()
            atualizar_lista(main_window)
        else:
            sg.popup_error("Usuário ou senha incorretos!")

    # Criar novo usuário
    if event == "Criar Usuário" and window == login_window:
        create_user_window = tela_criar_usuario()

    if event == "Salvar Usuário" and window == create_user_window:
        novo_usuario = values['-NEW_USER-'].strip()
        nova_senha = values['-NEW_PASSWORD-'].strip()
        confirmar_senha = values['-CONFIRM_PASSWORD-'].strip()

        if not novo_usuario or not nova_senha or not confirmar_senha:
            sg.popup_error("Por favor, preencha todos os campos.")
            continue

        if novo_usuario in usuarios:
            sg.popup_error("Usuário já existe.")
            continue

        if nova_senha != confirmar_senha:
            sg.popup_error("As senhas não coincidem.")
            continue

        usuarios[novo_usuario] = criar_hash(nova_senha)
        salvar_dados(USERS_FILE, usuarios)
        sg.popup("Usuário criado com sucesso!")
        create_user_window.close()

    # Fechar janela principal
    if event in (sg.WINDOW_CLOSED, "Sair") and window == main_window:
        salvar_dados(DATABASE_FILE, pecados)
        break

    # Adicionar um novo pecado
    if event == "Adicionar" and window == main_window:
        pecado = values['-PECADO-'].strip()
        data = values['-DATA-'].strip()

        if not pecado or not data:
            sg.popup_error("Por favor, preencha o nome do pecado e a data.")
            continue

        if calcular_dias(data) == "Data inválida":
            sg.popup_error("Data inválida. Use o formato dd/mm/aaaa.")
            continue

        if pecado not in pecados:
            pecados[pecado] = {"data": data, "historico": [data]}
        else:
            pecados[pecado]["data"] = data
            pecados[pecado]["historico"].append(data)

        salvar_dados(DATABASE_FILE, pecados)
        atualizar_lista(main_window)
        window['-PECADO-'].update("")
        window['-DATA-'].update("")
        sg.popup(f"Pecado '{pecado}' adicionado/atualizado com sucesso!")

    # Atualizar pecado existente
    if event == "Atualizar Pecado" and window == main_window:
        selecionado = values['-LISTA-']
        if not selecionado:
            sg.popup_error("Selecione um pecado para atualizar.")
            continue

        

        pecado_selecionado = selecionado[0].split(" - ")[0].replace("Pecado: ", "")
        nova_data = sg.popup_get_text(f"Digite a nova data para '{pecado_selecionado}' (dd/mm/aaaa):")

        if not nova_data or calcular_dias(nova_data) == "Data inválida":
            sg.popup_error("Data inválida ou operação cancelada.")
            continue

        pecados[pecado_selecionado]["data"] = nova_data
        pecados[pecado_selecionado]["historico"].append(nova_data)
        salvar_dados(DATABASE_FILE, pecados)
        atualizar_lista(main_window)
        sg.popup("Pecado atualizado com sucesso!")

    # Remover pecado
    if event == "Remover Pecado" and window == main_window:
        selecionado = values['-LISTA-']
        if not selecionado:
            sg.popup_error("Selecione um pecado para remover.")
            continue

        pecado_selecionado = selecionado[0].split(" - ")[0].replace("Pecado: ", "")
        pecados.pop(pecado_selecionado, None)
        salvar_dados(DATABASE_FILE, pecados)
        atualizar_lista(main_window)
        sg.popup("Pecado removido com sucesso!")


    # Visualizar detalhes
    if event == "Visualizar Detalhes" and window == main_window:
        selecionado = values['-LISTA-']
        if not selecionado:
            sg.popup_error("Selecione um pecado para visualizar.")
            continue

        pecado_selecionado = selecionado[0].split(" - ")[0].replace("Pecado: ", "")
        info = pecados[pecado_selecionado]
        dias_sem_cometer = calcular_dias(info["data"])
        historico = "\n".join(info["historico"])
        sg.popup(f"Pecado: {pecado_selecionado}\nÚltima Data: {info['data']}\nDias sem cometer: {dias_sem_cometer}\nHistórico:\n{historico}")


if login_window:
    login_window.close()
if main_window:
    main_window.close()
if create_user_window:
    create_user_window.close()