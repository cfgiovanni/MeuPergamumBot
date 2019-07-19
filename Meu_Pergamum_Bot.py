from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException 

import datetime
import time
import pandas as pd
import telepot

# Dados do usuário

RA = ''
SENHA = ''
TOKEN_TELEGRAM = ''
NR_TELEGRAM = DIGITE NUMERO

#

class bibliobot:
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        # chromedriver.exe on path
        self.driver = webdriver.Chrome()
        
    def CloseBrowser(self):
        self.driver.close()

    def Quit(self):
        self.driver.quit()
        
    def login(self):
        driver = self.driver
        driver.get("http://biblioteca.utfpr.edu.br/pergamum/biblioteca_s/php/login_usu.php?flag=index.php")
        time.sleep(1)
        self.driver.implicitly_wait(10)
        user_name_elem = driver.find_element_by_xpath("//input[@name='login']")
        user_name_elem.clear()
        user_name_elem.send_keys(self.username)
        password_elem = driver.find_element_by_xpath("//input[@name='password']")
        password_elem.clear()
        password_elem.send_keys(self.password)        
        password_elem.send_keys(Keys.RETURN)      
    
    def logout(self):
        self.driver.implicitly_wait(2)
        logout_button = self.driver.find_element_by_xpath("//img[@class='btn_sair']") 
        logout_button.click()
        
    def renovar(self, idx):
        self.driver.implicitly_wait(6)
        renew_button = self.driver.find_elements_by_xpath("//input[@class='btn_renovar']")
        return renew_button[idx].click()
            
    def reservado(self):
        self.driver.implicitly_wait(2)
        try:
            titulo_reservado = self.driver.find_element_by_xpath("//span[@class='txt_alert_nao']")
        except NoSuchElementException:
            return False
        return True
        
    def voltar(self):
        # espera ate 4 seg para achar o botao voltar
        self.driver.implicitly_wait(4)
        voltar_button = self.driver.find_element_by_xpath("//input[@class='btn_voltar']")
        voltar_button.click()
        
    def titulo(self):
        titulo_elem = self.driver.find_elements_by_xpath("//a[@class='txt_azul']")
        titulos = [x.text for x in titulo_elem]
        return titulos
   
    def lista_retorno_renovacoes(self):
        self.driver.implicitly_wait(10)
        data_elem = self.driver.find_elements_by_xpath("//td[@class='txt_cinza_10']")
        data_retorno = [x.text for x in data_elem]
        return data_retorno

# bot que enviara msg pelo telegram
# token específico do usuário
bot = telepot.Bot(TOKEN_TELEGRAM)

BiblioUser = bibliobot(RA,SENHA)
#login
BiblioUser.login()

#lista titulos emprestados
titulos = BiblioUser.titulo()
# index da data de devolucao para 5 livros (maximo)
idx = [3,6,9,12,15]
#numero de livros emprestados 
numero_titulos = len(BiblioUser.titulo())
#index para o numero de livro emprestados pelo usuario
data_idx = idx[:numero_titulos]
#data para retorno dos livros
data_retorno = [BiblioUser.lista_retorno_renovacoes()[x] for x in data_idx]

#index para lista do numero de renovacoes
renovacoes_idx = [x+1 for x in data_idx] #[4,7,10,13,16]
#lista do numero de renovacoes feitas pelo ususario
nr_renovacoes = [BiblioUser.lista_retorno_renovacoes()[x] for x in renovacoes_idx]

# funcao para pegar dia anterior a devolucao
def dia_anterior(date_str):
    format_str = '%d/%m/%Y' # format
    #pega a data de devolucao como str e transforma em formato datetime
    datetime_obj = datetime.datetime.strptime(date_str, format_str) 
    #dia anterior a data de devolucao em datetime
    dia_anterior_date_time = datetime_obj - datetime.timedelta(days=1)
    # dia anterior em str
    dia_anterior = dia_anterior_date_time.strftime('%d/%m/%Y')
    return dia_anterior

#lista com os dias anteriores as devolucoes
dia_anterior = [dia_anterior(x) for x in data_retorno]

# criacao de uma dataframe com os dados
df = pd.DataFrame({'Titulo': titulos,'DataRetorno':data_retorno, 'DiaAnterior':dia_anterior, 'Renovacoes':nr_renovacoes},
                  columns=['Titulo', 'DataRetorno', 'DiaAnterior', 'Renovacoes'])


# variavel str do dia atual
hoje = datetime.datetime.today().strftime('%d/%m/%Y')

# lista com os index dos livros que precisam ser renovados (vencem no dia seguinte)
#checa se o hoje (ou amanha se nao logar hoje) e o dia anterior ao vencimento do emprestimo
idx_titulos_que_venceram_emprestimo_semanal = df[(df.DiaAnterior == hoje) | (df.DataRetorno == hoje)].index.tolist()

#index dos titulos que ja foram reservados 3 vezes
idx_titulos_que_venceram_limite_emprestimo = df[df.Renovacoes == '3 / 3'].index.tolist()

# index dos livros que ja foram renovados 3 vezes e que precisam ser devolvidos ate amanha
idx_titulos_para_devolver = [x for x in idx_titulos_que_venceram_emprestimo_semanal 
                             if x in idx_titulos_que_venceram_limite_emprestimo]

#se a lista dos livros que precisam ser devolvidos nao e vazia:
if idx_titulos_para_devolver:
    #para cada livro que precisa ser devolvido ate amanha, enviar msg avisando
    for i in idx_titulos_para_devolver:
        msg = '{} - **O LIVRO** \n\n"{}" \n\n**PRECISA SER DEVOLVIDO ATÉ AMANHÃ** ({})'.format(hoje, 
                                                                                        df.iloc[i,0], df.iloc[i,1])
        #parse_mode para mostrar negrito na msg
        bot.sendMessage(NR_TELEGRAM, msg, parse_mode= 'Markdown')
else:
    pass

# index dos titulos que venceram emprestimo semanal e ainda podem ser renovados
idx_titulos_para_renovar = [x for x in idx_titulos_que_venceram_emprestimo_semanal if x not in idx_titulos_para_devolver]

#se a lista nao e vazia
if idx_titulos_para_renovar:
    for idx in idx_titulos_para_renovar:
        BiblioUser.renovar(idx)
        time.sleep(1)
        BiblioUser.voltar()
#se a lista e vazia pule a funcao renovar os titulos
else: 
    pass

# nova df

titulos = BiblioUser.titulo()
data_retorno = [BiblioUser.lista_retorno_renovacoes()[x] for x in data_idx]
nr_renovacoes = [BiblioUser.lista_retorno_renovacoes()[x] for x in renovacoes_idx]
df_pos = pd.DataFrame({'Titulo': titulos,'DataRetorno':data_retorno,'Renovacoes':nr_renovacoes},
                  columns=['Titulo', 'DataRetorno', 'Renovacoes'])


time.sleep(1)
BiblioUser.logout()

time.sleep(1)
BiblioUser.CloseBrowser()

time.sleep(1)
BiblioUser.Quit()

#enviar msg com os titulos renovados
#so envia se lista de index nao for vazia
for index in idx_titulos_para_renovar:
    
    titulo_renovado = df_pos.iloc[index,0]
    nova_data_entrega = df_pos.iloc[index,1]
    nr_renovacoes = df_pos.iloc[index,2]
    #msg = 'Título: ' + titulo_renovado + '\nVencimento: '+ nova_data_entrega + '\nRenovações: ' + nr_renovacoes
    #msg = 'Título: %s \nVencimento: %s \nRenovações: %s' %(titulo_renovado, nova_data_entrega, nr_renovacoes)
    
    #checando se o livro foi reservado e nao foi possivel fazer a reserva:
    if df_pos.iloc[index,2] == df.iloc[index,3]:
        msg = '{} - **LIVRO ESTÁ RESERVADO** \n\nTítulo: "{}" \nVencimento: {} \nRenovações: {}'.format(hoje,
                                                            titulo_renovado, nova_data_entrega, nr_renovacoes)
    else:
        msg = '{} - **LIVRO RENOVADO** \n\nTítulo: "{}" \nVencimento: {} \nRenovações: {}'.format(hoje, titulo_renovado, 
                                                                                        nova_data_entrega, nr_renovacoes)
    bot.sendMessage(NR_TELEGRAM, msg, parse_mode= 'Markdown')



