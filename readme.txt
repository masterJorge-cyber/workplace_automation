🚀 NF-SCRAPER - SISTEMA DE AUTOMAÇÃO DE NOTAS FISCAIS
=====================================================

📁 COMO USAR:

1. ✅ INSTALAÇÃO (FAZER UMA VEZ):
   - Execute o arquivo: instalar.bat
   - Aguarde a instalação completa (pode demorar alguns minutos)
   - Não feche a janela durante o processo

2. 🎯 EXECUÇÃO (USAR SEMPRE):
   - Execute o arquivo: executar.bat
   - O sistema vai iniciar automaticamente

📄 CONFIGURAÇÃO DOS ARQUIVOS:

✏️ ARQUIVO: .env
---------------
Configure com suas credenciais de acesso:

EMAIL=seu_email@empresa.com
PASSWORD=sua_senha
MONITOR_USER=usuario_monitor  
MONITOR_PASSWORD=senha_monitor
PROXY_HOST=proxy_empresa.com
PROXY_PORT=8080
PROXY_USER=usuario_proxy
PROXY_PASSWORD=senha_proxy

📝 IMPORTANTE:
- Substitua pelos seus dados reais
- Mantenha o formato exato (sem espaços around do =)
- Não use aspas nos valores

✏️ ARQUIVO: notas_fiscais.json
-------------------------------
Adicione suas notas fiscais neste formato:

[
  {
    "chave": "35251047508411094037551100000220031339359138",
    "fiscal_doc_no": "220031",
    "location_id": "001",
    "series_no": "1",
    "protocolo": "",
    "chave_aux": "NF001"
  },
  {
    "chave": "35251047508411094037551100000220301339362217",
    "fiscal_doc_no": "220301",
    "location_id": "001", 
    "series_no": "1",
    "protocolo": "",
    "chave_aux": "NF002"
  }
]

📝 IMPORTANTE:
- Use chaves de acesso reais
- Mantenha a estrutura de colchetes e chaves
- Adicione quantas notas precisar

🛠️ SOLUÇÃO DE PROBLEMAS:

❌ Se aparecer erro de bibliotecas:
   - Execute instalar.bat novamente

❌ Se aparecer erro de Chromium:
   - O instalador já inclui o Chromium, mas se der erro execute novamente

❌ Se o sistema não encontrar as notas:
   - Verifique o formato do arquivo notas_fiscais.json
   - Use https://jsonformatter.org para validar o JSON

📞 SUPORTE:
Em caso de problemas, verifique:
1. ✅ .env configurado corretamente
2. ✅ notas_fiscais.json no formato JSON válido
3. ✅ instalar.bat executado com sucesso

🎯 FLUXO CORRETO:
instalar.bat → executar.bat → SUCESSO!

================================================================
CONFIGURAÇÃO DOS ARQUIVOS .env E notas_fiscais.json
================================================================

📋 ARQUIVO .env - CREDENCIAIS DE ACESSO:
----------------------------------------
EDITE O ARQUIVO .env COM SEUS DADOS:

EMAIL=seu_email_real@empresa.com
PASSWORD=sua_senha_real
MONITOR_USER=seu_usuario_monitor
MONITOR_PASSWORD=sua_senha_monitor

📋 ARQUIVO notas_fiscais.json - DADOS DAS NOTAS:
------------------------------------------------
EDITE O ARQUIVO notas_fiscais.json COM SUAS NOTAS:

[
  {
    "chave": "CHAVE_DE_ACESSO_DA_NOTA_1",
    "fiscal_doc_no": "NUMERO_DOCUMENTO_1", 
    "location_id": "001",
    "series_no": "1",
    "protocolo": "",
    "chave_aux": "MINHA_NOTA_1"
  },
  {
    "chave": "CHAVE_DE_ACESSO_DA_NOTA_2",
    "fiscal_doc_no": "NUMERO_DOCUMENTO_2",
    "location_id": "001",
    "series_no": "1", 
    "protocolo": "",
    "chave_aux": "MINHA_NOTA_2"
  }
]

⚡ DICAS RÁPIDAS:
- Use notas fiscais REAIS no JSON
- Configure credenciais VÁLIDAS no .env
- Execute instalar_tudo_completo.bat APENAS UMA VEZ
- Use executar.bat SEMPRE que for usar o sistema

================================================================