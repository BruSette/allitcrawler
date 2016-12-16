from urllib.request import urlopen
import os
from bs4 import BeautifulSoup
from urllib.error import HTTPError
import psycopg2
from curses.ascii import NUL
from apt.auth import update

"""
DEFINE UMA VARIÁVEL INICIAL PARA A URL
"""
START_URL = ("http://www.allitebooks.com/")

downloads = []
downloadsError = []

def quant_pags():
    try:
        html = urlopen(START_URL)
    except:
        quant_pags()
        print("Erro na conexão. Verifique a conexão com a internet")
        return None
    bsObj = BeautifulSoup(html.read(), "html.parser")
    nameList = bsObj.findAll("a", {"title":"Last Page →"})
    for name in nameList:
        cont = int(name.getText())
    return cont


def get_links(url):
    html = urlopen(url)
    try:
        bsObj = BeautifulSoup(html.read(), "html.parser")
    except:
        get_links(url)
        print("Erro na conexão. Verifique a conexão com a internet")
        return None
    links = bsObj.findAll("h2",{"class":"entry-title"})
    for link in links:
        '''print(link.find("a").attrs['href'])'''
        name = link.find("a").getText()
        print("Baixando livro: "+name)
        name = str(name).replace("/", "")
        download_link(link.find("a").attrs['href'],name)


def download_link(url,name):
    try:
        html = urlopen(url)
    except HTTPError as e:
        print("Error to open file link " )
        return None

    try:
        bsObj = BeautifulSoup(html.read(), "html.parser")
    except:
        download_link(url,name)
        print("Erro na conexão. Verifique a conexão com a internet")
    links = bsObj.find("span",{"class":"download-links"})
    '''print (type(links))'''
    try:
        links = links.find("a").attrs['href']
        links = str(links).replace(" ","%20")
        isbns = bsObj.find("div",{"class":"book-detail"})
        isbns = bsObj.findAll("dd")
        cont = 1;
        for isbn in  isbns:
            if (cont == 2):
               break
            cont = cont +1

        isbn = isbn.getText()
        isbn = str(isbn).replace(" ", "")
    except:
        try:
            baixado(name,isbn,"false")
        except:
            print("Erro ao baixar o livro: "+name +". Verifique o link do mesmo ")
        return None
    try:
        download  = urlopen(links)
    except HTTPError as e:
        print("Error to open file link")
        if not baixado(name,isbn,"false"):
            update(isbn,"false")

        return None

    file_path = os.path.join('/home/bruno/Livros/'+ name+'.pdf')
    print("Salvando em: "+file_path)
    if baixado(name,isbn,"true"):
        file = open(file_path, 'wb')
        file.write(download.read())
        file.close()
        ''''gerar_arquivo(links,name)'''
        print("Livro baixado com sucesso")
    else:
        if (verificalivro(isbn)):
            update(isbn, "true")
            file = open(file_path, 'wb')
            file.write(download.read())
            file.close()
        else:
            print("Livro ja baixado: " +name + ",verifique seus arquivos e seu banco de dados")


def verificalivro(isbn):
    try:
        ''''CRIAR DATABASE livros no postgres e definir senha como 123'''
        conn = psycopg2.connect("dbname='livros' user='postgres' host='localhost' password='123'")
    except:
        print ("I am unable to connect to the database")
        return 0
    cur = conn.cursor()
    try:
        cur.execute("SELECT * from livros where baixado = false and isbn=%(id)s",{'id':isbn})
        rows = cur.fetchone()
        if (rows):
            if conn:
                conn.close()
            return 1
        else:
            if conn:
                conn.close()
            return 0
    except:
        print("Não foi possivel selecionar")
        if conn:
            conn.close()
        return 0


def baixado(name,isbn,baixado):
    try:
        conn = psycopg2.connect("dbname='livros' user='postgres' host='localhost' password='123'")
    except:
        return 0
        print ("I am unable to connect to the database")
    cur = conn.cursor()
    ''''criar tabela livros com campos isbn varchar(100),nome varchar(100),baixado boolean'''
    sql = "INSERT INTO livros (isbn,nome,baixado) VALUES ('"+isbn+"','"+name+"',"+baixado+")"
    print(sql)
    try:
        cur.execute(sql)
        conn.commit()
        if conn:
            conn.close()
        return 1
    except:
        print("Erro na inserção")
        if conn:
            conn.close()
        return 0

def update(isbn,baixado):
    try:
        conn = psycopg2.connect("dbname='livros' user='postgres' host='localhost' password='123'")
    except:
        return 0
        print ("I am unable to connect to the database")

    cur = conn.cursor()
    sql = "UPDATE livros set baixado ="+baixado +" where isbn='"+ isbn +"'"
    print(sql)
    try:
        cur.execute(sql)
        conn.commit()
        if conn:
            conn.close()
        return 1
    except:
        if conn:
            conn.close()
        return 0


def gerar_arquivo(url,name):
    file_path = os.path.join(os.path.dirname(__file__)+"/saida", 'downloads.txt')
    downloads.append(url +';'+ name + '\n')
    with open(file_path, "w") as fp:
        fp.writelines(downloads)
    fp.close()



def gerar_arquivo_erro(url,name):
    file_path = os.path.join(os.path.dirname(__file__)+"/saida", 'downloads-erros.txt')
    downloadsError.append(url +';'+ name + '\n')
    with open(file_path, "w") as fp:
        fp.writelines(downloadsError)

    fp.close()

"""
    MÉTODO PRINCIPAL
"""
try:
    conn = psycopg2.connect("dbname='livros' user='postgres' host='localhost' password='123'")
except:
    print ("I am unable to connect to the database")

quantPages = quant_pags()
NEW_URL = START_URL + "page/"
try:
    os.mkdir("/home/bruno/Livros")
    print("Pasta já criada com sucesso\n")
except FileExistsError:
    print("Pasta já criada\n")


for i in range(1,quantPages+1):
    url = NEW_URL + str(i)
    get_links(url)
