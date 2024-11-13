import sys
import time
import os
import shutil

# Classe que representa um nó em uma Trie
class TrieNode:
    def __init__(self):
        # Inicializa um nó da Trie que contém os filhos e o código
        self.children = {}  # Dicionário para armazenar os filhos deste nó, mapeados por caracteres
        self.code = None  # Código associado a este nó, usado na compressão

# Classe que representa a Trie utilizada para a compressão LZW
class Trie:
    def __init__(self):
        # Inicializa a Trie com um nó raiz e define o próximo código disponível
        self.root = TrieNode()  # O nó raiz da Trie
        self.next_code = 256  # Inicialmente, para caracteres ASCII, começando a partir de 256 para novos códigos

    # Método para inserir uma sequência de bytes e associar um código a ela
    def insert(self, key, code):
        # Navega pela Trie e insere um nó correspondente a cada byte da sequência
        node = self.root
        for char in key:
            if char not in node.children:
                node.children[char] = TrieNode()  # Cria um novo nó se o caractere não está presente
            node = node.children[char]  # Move-se para o próximo nó na sequência
        node.code = code  # Associa o código ao nó correspondente

    # Método para procurar uma sequência de bytes e retornar seu código
    def search(self, key):
        # Navega pela Trie para tentar localizar a sequência e retornar seu código
        node = self.root
        for char in key:
            if char in node.children:
                node = node.children[char]  # Avança na Trie se o caractere está presente
            else:
                return None  # Retorna None se a sequência não for encontrada
        return node.code

    # Método para obter o próximo código disponível
    def get_next_code(self):
        # Retorna o próximo código disponível e o incrementa
        code = self.next_code
        self.next_code += 1  # Incrementa o código para o próximo uso
        return code

# Função para comprimir dados usando o algoritmo LZW
# input_bytes: sequência de bytes a ser comprimida
# max_bits: limite máximo para os bits usados
# variable_bits: flag indicando se o tamanho dos bits é variável
# Retorna uma lista de códigos comprimidos e o tamanho do código final

def lzw_compress(input_bytes, max_bits=12, variable_bits=False):
    # Define o tamanho máximo da tabela com base no número máximo de bits
    max_table_size = 2 ** max_bits  # Tamanho máximo da tabela
    trie = Trie()  # Cria uma nova Trie para armazenar as sequências

    # Inicializar a tabela com caracteres ASCII (códigos 0 a 255)
    for i in range(256):
        trie.insert(bytes([i]), i)  # Cada caractere ASCII é inserido na Trie com seu respectivo código

    current_bytes = b""  # Sequência atual de bytes sendo processada
    compressed_data = []  # Lista para armazenar os códigos resultantes da compressão

    # Tamanho atual do código, inicialmente 9 bits se for variável
    current_code_size = 9 if variable_bits else max_bits  # Começamos com 9 bits se for variável
    max_table_size = 2 ** current_code_size  # Atualiza o tamanho máximo da tabela com base nos bits atuais

    # Percorre cada byte da entrada
    for byte in input_bytes:
        new_bytes = current_bytes + bytes([byte])  # Concatena o byte atual com a sequência atual
        if trie.search(new_bytes) is not None:
            # Se a sequência estiver na Trie, continua concatenando
            current_bytes = new_bytes
        else:
            # Se a sequência não estiver na Trie, processa a sequência atual
            compressed_data.append(trie.search(current_bytes))  # Armazena o código da sequência atual
            if trie.next_code < max_table_size:
                trie.insert(new_bytes, trie.get_next_code())  # Insere a nova sequência na Trie
            current_bytes = bytes([byte])  # Reinicia a sequência atual

            # Se os bits são variáveis e atingimos o tamanho máximo, aumente o tamanho do código
            if variable_bits and trie.next_code >= max_table_size and current_code_size < max_bits:
                current_code_size += 1  # Aumenta o tamanho do código
                max_table_size = 2 ** current_code_size  # Atualiza o tamanho da tabela

    # Se restar alguma sequência, armazena o código dela
    if current_bytes:
        compressed_data.append(trie.search(current_bytes))

    return compressed_data, current_code_size  # Retorna os códigos comprimidos e o tamanho do código

# Função para descomprimir dados comprimidos com LZW
# compressed_data: sequência de códigos a serem descomprimidos
# max_bits: limite máximo para os bits usados
# variable_bits: flag indicando se o tamanho dos bits é variável
# Retorna os dados descomprimidos como bytes

def lzw_decompress(compressed_data, max_bits=12, variable_bits=False):
    # Define o tamanho do código atual e o tamanho máximo da tabela
    current_code_size = 9 if variable_bits else max_bits  # Define o tamanho do código inicial
    max_table_size = 2 ** current_code_size  # Define o tamanho máximo da tabela com base nos bits
    table = {i: bytes([i]) for i in range(256)}  # Inicializa a tabela com códigos ASCII (0 a 255)
    next_code = 256  # Próximo código disponível para ser adicionado à tabela

    # Remove e usa o primeiro código comprimido
    current_code = compressed_data.pop(0)  # Obtém o primeiro código da lista comprimida
    current_bytes = table[current_code]  # Recupera a sequência correspondente ao código atual
    decompressed_data = [current_bytes]  # Inicializa a lista de dados descomprimidos

    # Itera sobre os códigos restantes
    for code in compressed_data:
        if code in table:
            # Se o código estiver na tabela, obtém a sequência correspondente
            entry = table[code]
        elif code == next_code:
            # Caso especial para sequência repetida (sequência + seu primeiro caractere)
            entry = current_bytes + current_bytes[:1]
        else:
            raise ValueError("Erro na descompressão: código inválido.")  # Código inválido na descompressão

        decompressed_data.append(entry)  # Adiciona a sequência descomprimida à lista de saída

        # Adiciona a nova sequência à tabela de códigos
        if next_code < max_table_size:
            table[next_code] = current_bytes + entry[:1]  # Adiciona nova sequência (sequência + primeiro caractere de entry)
            next_code += 1

        # Se estamos usando tamanho de bits variável, aumente o tamanho conforme necessário
        if variable_bits and next_code >= max_table_size and current_code_size < max_bits:
            current_code_size += 1  # Aumenta o tamanho do código
            max_table_size = 2 ** current_code_size  # Atualiza o tamanho da tabela

        current_bytes = entry  # Atualiza a sequência atual para a próxima iteração

    return b''.join(decompressed_data)  # Retorna os dados descomprimidos como uma única sequência de bytes

# Função para limpar os diretórios compressed e decompressed
# Apaga todos os arquivos contidos nesses diretórios de forma independente

def clear_directories():
    directories = ["compressed/", "decompressed/"]
    for directory in directories:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)  # Remove o arquivo
            except Exception as e:
                print(f"Erro ao apagar o arquivo {file_path}: {e}")

# Ponto de entrada do script
if __name__ == "__main__":
    # Se o comando for para limpar os diretórios, executa a função correspondente
    if len(sys.argv) == 2 and sys.argv[1] == "clear":
        clear_directories()
        print("Diretórios 'compressed' e 'decompressed' limpos com sucesso.")
        sys.exit(0)

    # Verifica se os argumentos fornecidos são suficientes
    if len(sys.argv) < 4:
        print("Uso: python lzw.py <compress|decompress> <arquivo> <f|v> [max_bits]")
        sys.exit(1)  # Encerra o programa se os argumentos não forem suficientes

    mode = sys.argv[1]  # Modo de operação: compress ou decompress
    file_path = sys.argv[2]  # Caminho do arquivo a ser processado
    version = sys.argv[3].lower()  # Versão: f (fixa) ou v (variável)
    max_bits = int(sys.argv[4]) if len(sys.argv) > 4 else 12  # Número máximo de bits (padrão é 12)

    variable_bits = version == 'v'  # Define se o tamanho dos bits é variável (True se versão for 'v')

    # Define os diretórios de trabalho
    base_dir = "original/"  # Diretório dos arquivos originais
    compressed_dir = "compressed/"  # Diretório onde os arquivos comprimidos serão salvos
    decompressed_dir = "decompressed/"  # Diretório onde os arquivos descomprimidos serão salvos

    file_name = os.path.basename(file_path)  # Obtém o nome do arquivo sem o caminho
    file_base_name, file_extension = os.path.splitext(file_name)  # Separa o nome base da extensão do arquivo

    start_time = time.time()  # Marca o tempo de início da execução para medir o desempenho

    if mode == "compress":
        # Caminho de entrada e saída para compressão
        input_path = os.path.join(base_dir, file_name)  # Caminho completo do arquivo de entrada
        if file_extension == '.txt':
            output_path = os.path.join(compressed_dir, f"{file_base_name}.txt")  # Mantém a extensão se for txt
        else:
            output_path = os.path.join(compressed_dir, f"{file_name}.txt")  # Adiciona .txt se a extensão não for txt

        # Lê os dados do arquivo de entrada para comprimir
        with open(input_path, 'rb') as file:
            data = file.read()
        # Comprime os dados usando a função lzw_compress
        compressed, final_code_size = lzw_compress(data, max_bits, variable_bits)
        # Grava os dados comprimidos no arquivo de saída
        with open(output_path, 'w') as file:
            file.write(' '.join(map(str, compressed)))  # Converte os códigos para string e escreve no arquivo
        print(f"Arquivo comprimido salvo como {output_path}")

        # Calcula e exibe a taxa de compressão
        original_size = os.path.getsize(input_path)  # Tamanho do arquivo original
        compressed_size = os.path.getsize(output_path)  # Tamanho do arquivo comprimido
        compression_ratio = original_size / compressed_size  # Calcula a taxa de compressão
        print(f"Taxa de compressão: {compression_ratio:.2f}")
        print(f"Bits utilizados: {final_code_size}")

    elif mode == "decompress":
        # Caminho de entrada e saída para descompressão
        input_path = os.path.join(compressed_dir, file_name)  # Caminho completo do arquivo comprimido

        # Verificar se o arquivo tem extensão .txt para remover apenas se necessário
        if file_extension == '.txt' and '.' in file_base_name:
            base_name, original_extension = file_base_name.rsplit('.', 1)  # Separa o nome base e a última extensão
            output_path = os.path.join(decompressed_dir, f"{base_name}.{original_extension}")
        else:
            output_path = os.path.join(decompressed_dir, f"{file_base_name}{file_extension}")

        # Lê os dados comprimidos do arquivo de entrada
        with open(input_path, 'r') as file:
            compressed_content = file.read().strip()  # Lê todo o conteúdo e remove espaços em branco
            if not compressed_content:
                print("Erro: Arquivo de compressão vazio ou inválido.")
                sys.exit(1)  # Encerra o programa em caso de erro
            compressed = list(map(int, compressed_content.split()))  # Converte o conteúdo para uma lista de inteiros
        # Descomprime os dados usando a função lzw_decompress
        decompressed = lzw_decompress(compressed, max_bits, variable_bits)
        # Grava os dados descomprimidos no arquivo de saída
        with open(output_path, 'wb') as file:
            file.write(decompressed)  # Escreve os dados descomprimidos em modo binário
        print(f"Arquivo descomprimido salvo como {output_path}")

        # Calcula e exibe a taxa de descompressão
        compressed_size = os.path.getsize(input_path)  # Tamanho do arquivo comprimido
        decompressed_size = os.path.getsize(output_path)  # Tamanho do arquivo descomprimido
        compression_ratio = decompressed_size / compressed_size  # Calcula a taxa de descompressão
        print(f"Taxa de descompressão: {compression_ratio:.2f}")
        print(f"Bits utilizados: {max_bits}")

    else:
        print("Modo desconhecido. Use 'compress' ou 'decompress'.")  # Mensagem de erro para modo inválido

    end_time = time.time()  # Marca o tempo de fim da execução
    print(f"Tempo de execução: {end_time - start_time:.2f} segundos")  # Exibe o tempo total de execução
