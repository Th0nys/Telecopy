def ola():
    return '👋 Olá!\n\nEu sou o Telecopy, seu assistente virtual para alterar e enviar mensagens de forma rápida e eficiente.\n\nEstou aqui para facilitar a sua vida! 😎\n\nEntão, vamos começar? Escolha uma das opções abaixo e vamos prosseguir juntos:'

def info():
    return """Vamos lá. Após contratar um de nossos planos um mar de possibilidades se abre.
Aqui na aba informações irei lhe explicar como é o meu funcionamento

- Você poderá escolher se quer enviar mensagens para grupos ou canais da sua lista de contatos.
- Modificaremos qualquer mensagem que voce escolher sem limites de caracteres.
- Após o término de sua assinatura o login terá que ser refeito"""
    
def planos():
    return """💥 Quer se destacar no mercado com um mar de possibilidades?💥

Nossas funcionalidades incríveis podem transformar a maneira como você se comunica e ajudá-lo a enviar mensagens que realmente causam um impacto. 

Com nossa ferramenta você poderá: 

1-Repassar mensagens 
2-Modificar mensagens
3-Alterar links 
4-Blacklist 
5-Bloqueio de imagens
6-Bloqueio de vídeos 
7-Bloqueio de áudios 

Você pode testar a ferramenta por 24h GRATUITAMENTE…

E quando quiser continuar usando nossos serviços, é simples! Basta adquirir por R$97,00, e sua ferramenta ficará liberada por 30 dias!

Não perca mais tempo, Escolha agora uma das opções abaixo e comece a enviar mensagens poderosas com o Telecopy! 💬"""


def set_groups():
    texto = """Para começar a repassar as mensagens de um grupo para outro, é simples! Basta ter o ID dos grupos em mãos, que você consegue ao clicar no botão "Ver Chats".

Instruções para uso:
/repassar <ação> <id_grupo_origem> <id_grupo_destino>

Ações possíveis:
- Adicionar (add): usando /repassar add você pode escolher de onde virá as mensagens e para onde vai.
	- Exemplo:
	   /repassar add -1001234567890 -1009876543210
	   
- Remover (remove): usando /repassar remove você pode remover um repasse que está ativo em sua conta.
	- Exemplo:
	  /repassar remove -1001234567890 -1009876543210"""
    return texto


def set_blacklist():
    texto = """Para bloquear certas mensagens de um grupo, é simples! Basta ter o ID do grupo, que você consegue ao clicar no botão "Ver Chats" e a palavra/frase que você quer bloquear.

Instruções para uso:
/blacklist <ação> <grupo_origem> "<palavra_proibida>"

Ações possíveis:
- Adicionar (add): usando /blacklist add você pode adicionar frases, colocando entre aspas ("frase tal"), que serão bloqueadas.
	- Exemplo:
	  /blacklist add -1001234567890 "frase de exemplo"
	  
- Remover (remove): usando /blacklist add você pode adicionar frases, colocando entre aspas ("frase tal"), que serão bloqueadas.
	- Exemplo:
	  /blacklist remove -1001234567890 "frase de exemplo" """

    return texto


def transform():
    texto = """Para transformar certas mensagens de um grupo, é simples! Basta ter o ID do grupo, que você consegue ao clicar no botão "Ver Chats", a palavra/frase que você deseja fazer a mudança e a palavra/frase que você deseja que fique na troca.

Instruções para uso:
/transformar <ação> <grupo_origem> "<frase para trocar>" "<frase trocada>"

Ações possíveis:
- Adicionar (add): usando /transformar add você pode escolher as frases para trocar, colocando entre aspas "frase exemplo 1" e depois como ela deverá ficar "frase exemplo 2".
	- Exemplo:
	 /transformar add -1001234567890 "frase como é" "frase como irá ficar"
	  
- Remover (remove): usando /transformar remove você pode escolher a frase que está salva e que deseja remover da conta, colocando entre aspas "frase como era" e a frase que era "frase como ficava".
	- Exemplo:
	  /transformar remove -1001234567890 "frase como é" "frase como irá ficar" """

    return texto

def email():
    texto = """Você também pode fazer algumas operações com o seu email:

Para trocar seu email cadastrado, digite:
/email troca seuemail@exemplo.com

Para remover seu email, digite:
/email remove seuemail@exemplo.com

Para verificar se você é um assinante, basta digitar o comando:
/email verifica seuemail@exemplo.com"""
    return texto

def logged():
    texto = 'Basta clicar nos botões para começar a configurar a ferramenta 👇'
    return texto

def trial():
    texto = f'''⏳ Seu teste grátis já foi garantido e você está a um passo de começar nesse mar de oportunidades, nossas funcionalidades foram liberadas GRATUITAMENTE por 24 horas ⏳

Após o teste, para continuar usando a ferramenta Telecopy, basta assinar nosso plano para continuar ativo o repasse das suas mensagens... 🚀'''

    return texto


def desbloq():
    texto = f'''Parabéns, o acesso ao Telecopy está sendo desbloqueado 🔓✅

Sua assinatura está ATIVA e ficará disponível por 30 dias. ♻️

Nós avisaremos quando o período estiver chegando ao fim…'''
    return texto
