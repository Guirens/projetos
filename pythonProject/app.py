import os
import sqlite3
import datetime
from flask import Flask, request, jsonify, render_template
import requests  # Para chamar a API de IA (Gemini AI)

# Criação do app Flask
app = Flask(__name__)

# Limite para upload de arquivos (16 MB no exemplo)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limita o tamanho do arquivo a 16 MB

# Cria uma conexão com o banco de dados SQLite
conn = sqlite3.connect('arquivos.db', check_same_thread=False)  # Parâmetro para evitar o erro 'database is locked'
cursor = conn.cursor()

# Cria a tabela para armazenar os metadados
cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS arquivos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        tipo TEXT,
        tamanho INTEGER,
        data_modificacao TEXT
    )
''')
conn.commit()

# Defina sua chave de API (substitua pelo valor real)
API_KEY = 'AIzaSyDpY3Gs6BZAn7GkpcHzIjx61Wv9P8n_3so'  # Substitua com a chave real da API

# Função genérica para detectar o tipo do arquivo via API (como Gemini AI)
def detectar_com_api(file_content):
    try:
        # Exemplo de chamada para uma API para detecção do tipo de arquivo
        headers = {
            'Authorization': f'Bearer {API_KEY}'  # Adicionando a chave de API no cabeçalho da requisição
        }

        # Fazendo a requisição POST com a chave da API
        response = requests.post(
            'https://api.gemini.com/detect',
            files={'file': file_content},
            headers=headers  # Adicionando o cabeçalho com a chave da API
        )

        if response.status_code == 200:
            # Supondo que a API de IA retorne um tipo MIME no campo "file_type"
            file_type = response.json().get('file_type', 'Unknown')
            return file_type
        else:
            print("Erro ao chamar a API de IA:", response.status_code)
            return 'Unknown'
    except Exception as e:
        print(f"Erro ao detectar o tipo de arquivo com API: {e}")
        return 'Unknown'

# Função para detectar e registrar os metadados
def detectar_e_registrar(nome_arquivo, file_content):
    try:
        # Detecta o tipo do arquivo via API (Gemini AI ou outra)
        tipo_arquivo = detectar_com_api(file_content)

        # Extrai os metadados do arquivo
        tamanho = len(file_content)  # O tamanho agora é baseado no conteúdo do arquivo
        data_modificacao = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Usando o timestamp atual

        # Insere os dados na tabela do banco de dados
        cursor.execute('''
            INSERT INTO arquivos (nome, tipo, tamanho, data_modificacao)
            VALUES (?, ?, ?, ?)
        ''', (nome_arquivo, tipo_arquivo, tamanho, data_modificacao))

        conn.commit()

        print(f"Arquivo '{nome_arquivo}' detectado como '{tipo_arquivo}'.")

    except Exception as e:
        print(f"Erro ao detectar e registrar o tipo de arquivo '{nome_arquivo}': {e}")

# Rota principal (página de upload)
@app.route('/')
def index():
    return render_template('index.html')

# Rota para o upload de arquivos
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # Lê o conteúdo do arquivo
        file_content = file.read()

        # Processa e registra os metadados
        detectar_e_registrar(file.filename, file_content)

        return jsonify({"message": f"Metadados do arquivo '{file.filename}' registrados com sucesso!"}), 200

# Rota para obter os metadados dos arquivos
@app.route('/metadata', methods=['GET'])
def get_metadata():
    cursor.execute('SELECT * FROM arquivos')
    rows = cursor.fetchall()

    metadata = []
    for row in rows:
        metadata.append({
            "ID": row[0],
            "File Name": row[1],
            "File Type": row[2],
            "Date Modified": row[3]
        })

    return jsonify(metadata)

if __name__ == '__main__':
    app.run(debug=True)
