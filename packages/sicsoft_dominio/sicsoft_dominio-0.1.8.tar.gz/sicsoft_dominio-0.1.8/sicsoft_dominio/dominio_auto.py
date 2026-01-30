from pywinauto.application import Application

from time import sleep
import subprocess
import os
import sys
from glob import glob


# poetry version

# poetry version patch
# poetry version minor
# poetry version major

# Gere os pacotes de distribuição
# poetry build

# Publique a nova versão no PyPI
# poetry publish

class App():
    def __init__(self, tipo, usuario, senha):
        '''
        Argumentos:
        1. 'escrita' ou 'fiscal'
        2. Login 
        3. Senha
        Cria uma instancia da aplicação com base no nome recebido
        '''
        # derruba o domínio
        derruba_dominio()

        while True:
            # inicia o domínio
            app = Application(backend='uia').start(rf"C:\Contabil\contabil.exe /{tipo}")
            app = Application(backend="uia").connect(title='Conectando ...',
                                                     timeout=120)

            # preenche o usuário e senha
            user_field = app.Conectando.child_window(auto_id="1005",
                                                     control_type="Edit").wrapper_object()
            user_field.set_text(usuario)

            password_field = app.Conectando.child_window(auto_id="1007",
                                                         control_type="Edit").wrapper_object()
            password_field.set_text(senha)

            # clica em ok
            button_ok = app.Conectando.child_window(title="OK", auto_id="1003",
                                                    control_type="Button").wrapper_object()
            button_ok.click()

            # verifica se o dominio já está sendo utilizado pelo número maximo de usuários permitidos.
            verificacao_nmu = verificar_usuarios_dominio()

            verificar_aviso_senha_periodica_dominio()

            # verifica se tem atualização
            atualizacao = verificar_atualizacao_dominio()

            if atualizacao:
                # atualiza o domínio
                atualizar_dominio()

            if verificacao_nmu:
                app.close()

            else:
                break

    def get_window(self, window):
        '''Retorna a janela principal para manipulações adicionais'''
        contador = 0
        while True:
            contador += 1
            try:
                app = Application().connect(title_re=f".*{window}.*", backend="uia",
                                            visible_only=True)
                self.main_window = app.window(title_re=f".*{window}.*")
                self.main_window.wait("ready", timeout=120)
                break
            except Exception:
                if contador == 120:
                    erro = 'Erro ao abrir o domínio'
                    print(erro)
                    print('O programa será encerrado em 30 segundos')
                    sleep(30)
                    sys.exit()
                sleep(1)
        return self.main_window

    def executar_comando(self, janela, comando):
        '''Executa um comando de teclado em uma janela'''

        janela.send_keystrokes(comando)

    def clicar(self, janela, titulo='', nome_classe='', double_click=False):

        if double_click:
            if titulo != '' and nome_classe != '':
                janela.child_window(title=titulo, class_name=nome_classe).double_click()

            elif titulo != "" and nome_classe == "":
                janela.child_window(title=titulo).double_click()

            elif titulo == "" and nome_classe != "":
                janela.child_window(class_name=nome_classe).double_click()
        else:
            if titulo != '' and nome_classe != '':
                janela.child_window(title=titulo, class_name=nome_classe).click()

            elif titulo != "" and nome_classe == "":
                janela.child_window(title=titulo).click()

            elif titulo == "" and nome_classe != "":
                janela.child_window(class_name=nome_classe).click()

    def receber_texto(self, janela, titulo='', nome_classe=''):

        if titulo != '' and nome_classe != '':
            janela.child_window(title=titulo, class_name=nome_classe).get_text()

        elif titulo != "" and nome_classe == "":
            janela.child_window(title=titulo).get_text()

        elif titulo == "" and nome_classe != "":
            janela.child_window(class_name=nome_classe).get_text()

    def selecionar_empresa(self, janela, codigo):
        empresa = janela.child_window(auto_id="lblEmpresa",
                                      control_type="DominioToolbar.LabelBase").window_text().split(
            ' ')[-1]

        if not empresa == codigo:

            janela.send_keystrokes('{F8}')

            # espera a janela troca de empresa carregar
            janela_troca_empresa = verificar_janela_abriu(
                main_window=janela,
                tipo=1,
                titulo='Troca de empresas',
                tempo=30)

            # seleciona busca por código
            radio_codigo = janela_troca_empresa.child_window(title="Código",
                                                             class_name="Button").is_checked()
            if not radio_codigo:
                checkbox = janela_troca_empresa.child_window(title="Código",
                                                             class_name="Button").wrapper_object()
                checkbox.click_input()

            # preenche o campo com o código da empresa
            sleep(2)
            janela_troca_empresa.child_window(
                class_name="Edit").wrapper_object().type_keys(codigo)
            sleep(2)
            janela_troca_empresa.type_keys('{ENTER}')

            # espera a janela troca de empresa fechar
            try:
                janela_troca_empresa.wait_not("exists", timeout=30)
            except Exception:
                return False
            else:
                return True
        else:
            return True
            # print(e)
            # erro = 'Erro ao selecionar empresa'
            # print(erro)
            # print('O programa será encerrado em 30 segundos')
            # sleep(30)
            # sys.exit()

    def verificar_empresa(self, janela, codigo):
        empresa = janela.child_window(auto_id="lblEmpresa",
                                      control_type="DominioToolbar.LabelBase").window_text().split(
            ' ')[-1]

        if empresa != codigo:

            return 'Empresa incorreta, abortando processo!'

        else:

            return 'Empresa selecionada com sucesso!'

    def derruba_dominio(self):
        '''
        Força o fechamento do domínio
        '''
        os.system("taskkill -F -IM Contabil.exe -T")


# atualizar domínio
def atualizar_dominio():
    '''
    Atualiza o domínio
    '''
    # obtem o path do executável de atualização
    path_executavel = obter_executavel_atualizacao(
        r'\\spt-dc1.forse.local\Dados\Publico\Giuliano\Dominio')

    # inicia o executável de atualização
    app = Application(backend="uia").start(path_executavel)

    # se conecta a janela de atualização
    app = Application().connect(
        title_re='.*Assistente de Atualização - Domínio Contábil*', timeout=60,
        backend="win32", visible_only=True)
    janela_atualizacao = app.window(
        title_re='.*Assistente de Atualização - Domínio Contábil*', visible_only=True)
    janela_atualizacao.wait("ready", timeout=30)

    # clicar em avançar 3 vezes
    btn_avancar = janela_atualizacao.child_window(title="&Avançar >",
                                                  class_name="TNewButton")
    for _ in range(4):
        btn_avancar.wait("ready", timeout=10)
        sleep(2)
        btn_avancar.click()

    # clicar em atualizar
    btn_atualizar = janela_atualizacao.child_window(title="&Atualizar",
                                                    class_name="TNewButton")
    btn_atualizar.wait("ready", timeout=10)
    btn_atualizar.click()

    # esperar a atualização terminar e clica em concluir
    contador = 0
    while True:
        contador += 1
        try:
            btn_concluir = janela_atualizacao.child_window(title="&Concluir",
                                                           class_name="TNewButton")
            btn_concluir.wait("ready", timeout=60)
            btn_concluir.click()
            break
        except:
            if contador == 600:
                erro = 'Erro ao atualizar o domínio'
                print(erro)
                print('O programa será encerrado em 30 segundos')
                sleep(30)
                sys.exit()
            sleep(1)
    sleep(2)


# verificar se a janela de nova versão apareceu
def verificar_atualizacao_dominio():
    '''
    Verifica se a janela de nova versão apareceu, se sim, fecha ela
    Args:
        None: None
    Return:
        True: janela apareceu e foi fechada
        False: janela não apareceu
    '''
    contador = 0
    while True:
        contador += 1
        try:
            app = Application().connect(title="Aviso", backend="uia", visible_only=True)
            janela_aviso = app.window(title="Aviso")
            janela_aviso.wait("ready", timeout=2)
            try:
                janela_aviso.child_window(title="&Não", class_name="Button").click()
                return True
            except:
                pass
        except Exception:
            if contador == 15:
                return False
        sleep(1)


def verificar_usuarios_dominio():
    """
    Função de retorna na classe se o dominio já está sendo utilizado pelo número maximo de usuários permitidos.
    """
    contador = 0
    while True:
        contador += 1
        try:
            app = Application().connect(title="Atenção!", backend="uia",
                                        visible_only=True)
            janela_aviso = app.window(title="Atenção!")
            janela_aviso.wait("ready", timeout=2)
            try:
                janela_aviso.child_window(title="&OK",
                                          class_name="Button").double_click()
                return True
            except:
                pass
        except Exception:
            if contador == 10:
                return False
        sleep(0.3)


def verificar_aviso_senha_periodica_dominio():
    contador = 0
    while True:
        contador += 1
        try:
            app = Application().connect(title="Aviso", backend="uia", visible_only=True)
            janela_aviso = app.window(title="Aviso")
            janela_aviso.wait("ready", timeout=2)
            try:
                janela_aviso.child_window(title="OK",
                                          class_name="Button").double_click()
                return
            except:
                pass
        except Exception:
            if contador == 10:
                return
        sleep(0.3)


def fechar_popup(janela):
    """
    Fecha o popup caso ele esteja presente na tela inicial do Domínio.
    """
    janela_avisos = verificar_janela_abriu(janela, 1, 'Avisos de Vencimento', 2)
    if not isinstance(janela_avisos, str):
        avisos = janela.child_window(title="&Fechar", class_name="Button")
        avisos.click()
    else:
        pass


def running(process_name):
    prog = [line.split() for line in subprocess.check_output("tasklist").splitlines()]
    [prog.pop(pr) for pr in [0, 1, 2]]  # useless
    for task in prog:
        if str(task[0]).replace("b'", "").replace("'", "") == process_name:
            return True
    return False


def verificar_janela_abriu(main_window, tipo, titulo, tempo):
    '''
    Tenta se conectar a uma janela específica, caso não consiga, encerra o programa
    Args:
        main_window: janela mãe
        titulo: título da janela filho que se deseja conectar
        tempo: tempo máximo de espera
    Return:
        janela: janela conectada
    '''
    try:
        contador = 0
        while True:
            contador += 1
            try:
                if tipo == 1:
                    janela = main_window.window(title=f"{titulo}")
                else:
                    janela = main_window.window(title_re=f".{titulo}.")
                janela.wait("ready", timeout=30)
                break
            except:
                if contador == tempo:
                    print(f'Erro ao abrir {titulo}')
                    print('O programa será encerrado em 30 segundos')
                    sleep(30)
                    sys.exit()
                    break
                sleep(1)

        return janela

    except Exception as e:
        erro = 'Erro ao verificar janela aberta'
        print(e, erro)
        return erro


# derruba o dominio
def derruba_dominio():
    '''
    Força o fechamento do domínio
    '''
    os.system("taskkill -F -IM Contabil.exe -T")


# abrir o domínio
def abrir_dominio(tipo, usuario, senha):
    '''
    Argumentos:
    1. 'escrita' ou 'fiscal'
    2. Login
    3. Senha
    Derruba o domínio e depois inicia ele. Verifica se possui alguma atualização (se sim atualiza e abre o domínio novamente, se não faz o login)
    '''
    # derruba o domínio
    derruba_dominio()

    while True:
        # inicia o domínio
        app = Application(backend='uia').start(rf"C:\Contabil\contabil.exe /{tipo}")
        app = Application(backend="uia").connect(title='Conectando ...')

        # preenche o usuário e senha
        user_field = app.Conectando.child_window(auto_id="1005",
                                                 control_type="Edit").wrapper_object()
        user_field.set_text(usuario)

        password_field = app.Conectando.child_window(auto_id="1007",
                                                     control_type="Edit").wrapper_object()
        password_field.set_text(senha)

        # clica em ok
        button_ok = app.Conectando.child_window(title="OK", auto_id="1003",
                                                control_type="Button").wrapper_object()
        button_ok.click()

        # verifica se tem atualização
        atualizacao = verificar_atualizacao_dominio()

        if atualizacao:
            # atualiza o domínio
            atualizar_dominio()
        else:
            break


# verificar se o domínio abriu
def conectar_janela_dominio(tipo_dominio):
    '''
    Conecta a janela principal do domínio. Caso de o timeout de 2 minutos, encerra o programa
    Return:
    main_window - janela principal do domínio
    É necessário dizer se o domínio é 'Escrita' ou 'Folha'
    '''
    contador = 0
    while True:
        contador += 1
        try:
            app = Application().connect(title_re=f".*Domínio {tipo_dominio}.*",
                                        backend="uia", visible_only=True)
            main_window = app.window(title_re=f".*Domínio {tipo_dominio}.*")
            main_window.wait("ready", timeout=120)
            break
        except Exception:
            if contador == 120:
                erro = 'Erro ao abrir o domínio'
                print(erro)
                print('O programa será encerrado em 30 segundos')
                sleep(30)
                sys.exit()
            sleep(1)

    return main_window


# verificar se a janela abriu
def verificar_janela_abriu(main_window, tipo, titulo, tempo):
    '''
    Tenta se conectar a uma janela específica, caso não consiga, encerra o programa
    Args:
        main_window: janela mãe
        titulo: título da janela filho que se deseja conectar
        tempo: tempo máximo de espera
    Return:
        janela: janela conectada
    '''
    contador = 0
    while True:
        contador += 1
        try:
            if tipo == 1:
                janela = main_window.window(title=f"{titulo}")
            else:
                janela = main_window.window(title_re=f".{titulo}.")
            janela.wait("ready", timeout=30)
            break
        except:
            if contador == tempo:
                print(f'Erro ao abrir {titulo}')
                print('O programa será encerrado em 30 segundos')
                sleep(30)
                sys.exit()
                break
            sleep(1)

    return janela


# selecionar empresa
def selecionar_empresa(main_window, codigo):
    '''
    Seleciona a empresa 176 (CIJUN) e espera a janela de troca de empresa fechar
    Args:
        main_window: janela principal
    '''
    # comando para selecionar empresa

    empresa = main_window.child_window(auto_id="lblEmpresa",
                                       control_type="DominioToolbar.LabelBase").window_text().split(
        ' ')[-1]

    if not empresa == codigo:

        # while not empresa == codigo:

        main_window.send_keystrokes('{F8}')

        # espera a janela troca de empresa carregar
        janela_troca_empresa = verificar_janela_abriu(
            main_window=main_window,
            tipo=1,
            titulo='Troca de empresas',
            tempo=30)

        # seleciona busca por código
        radio_codigo = janela_troca_empresa.child_window(title="Código",
                                                         class_name="Button").is_checked()
        if not radio_codigo:
            checkbox = janela_troca_empresa.child_window(title="Código",
                                                         class_name="Button").wrapper_object()
            checkbox.click_input()

        # preenche o campo com o código da empresa
        sleep(2)
        janela_troca_empresa.child_window(class_name="Edit").wrapper_object().type_keys(
            codigo)
        janela_troca_empresa.set_focus()
        sleep(2)
        janela_troca_empresa.type_keys('{ENTER}')

        # espera a janela troca de empresa fechar
    try:
        janela_troca_empresa.wait_not("exists", timeout=30)
    except Exception as e:
        print(e)
        erro = 'Erro ao fechar a janela de troca de empresa'
        print(erro)
        print('O programa será encerrado em 30 segundos')
        sleep(30)
        sys.exit()


# pegar path do executável de atualização do domínio
def obter_executavel_atualizacao(diretorio):
    '''
    Obtem o path do executável mais recente no diretório informado
    Args:
        diretorio: diretório onde se encontra o executável
    Return:
        executavel_mais_recente: path do executável mais recente
        False: caso não encontre nenhum executável
    '''
    # Define o padrão para buscar arquivos .exe no diretório
    tipo_arquivo = os.path.join(diretorio, "*.exe")

    # Busca por todos os arquivos .exe no diretório
    executaveis = glob(tipo_arquivo)

    # Verifica se encontrou algum arquivo .exe
    if not executaveis:
        return False

    # Retorna o executável mais recente com base na data de modificação
    executavel_mais_recente = max(executaveis, key=os.path.getmtime)
    return executavel_mais_recente


# salvar arquivo
def salvar_arquivo(diretorio):
    try:
        janela_salvar_como = Application().connect(title_re=f"Salvar como",
                                                   backend="win32", timeout=15,
                                                   visible_only=True).Salvarcomo
        janela_salvar_como.wait('ready', timeout=15)
    except:
        erro = 'Janela de salvar como não encontrada'
        print(erro)
        return erro

    janela_salvar_como.type_keys(
        fr'{diretorio.replace("(", "{(}").replace(")", "{)}")}', with_spaces=True)
    sleep(0.5)

    janela_salvar_como.type_keys('{TAB}')
    janela_salvar_como.type_keys('p')
    sleep(0.5)

    janela_salvar_como.Salvar.click_input()

    janela_salvar_como.wait_not('exists', timeout=15)

    return True



