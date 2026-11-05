# Estante de Livros do PPGD

Site estático com os livros do programa. O cadastro é feito em uma planilha Google, e uma rotina diária copia os dados e as capas para o site. Nenhum computador pessoal precisa ficar ligado.

## Como cadastrar um livro

1. Abra a planilha de cadastro, aba **Livros**, e preencha uma linha nova.
2. Confira se a coluna **O que falta** mostra "Completo".
3. Coloque **Sim** em **Publicar?**.

O livro aparece no site na atualização seguinte, feita todo dia às 6h (horário de Brasília). Para publicar na hora: no GitHub, abra **Actions**, depois **Atualizar e publicar a estante**, e clique em **Run workflow**.

Para tirar um livro do site, troque **Publicar?** para **Não**.

### Capas

- **Link da imagem:** cole na coluna **Capa** um link que abra direto a imagem (JPG, PNG ou WebP, até 5 MB). A rotina guarda uma cópia e o site deixa de depender desse link. Links de páginas do Drive não funcionam aqui.
- **Arquivo:** envie a imagem para a pasta `capas` no GitHub e escreva o nome do arquivo na coluna **Capa**.
- **Trocar uma capa:** a rotina não baixa de novo uma capa que já existe. Envie o arquivo novo para `capas` e escreva o nome dele na coluna **Capa**.

## Como saber se algo deu errado

Abra **Actions** no GitHub. Linhas com problema aparecem como `AVISO` no passo **Ler a planilha**, e essas linhas ficam fora do site até serem corrigidas.

Se a planilha não puder ser lida, ou se o número de livros cair para menos da metade, a atualização para e o site continua com a última versão boa. Se a queda for de propósito, rode **Run workflow** marcando **Aceitar uma queda grande no número de livros**.

Importante: o GitHub pode desativar rotinas agendadas depois de 60 dias sem atividade no repositório. O site continua no ar, mas para de atualizar sozinho. Para religar, abra **Actions** e clique em **Enable workflow**.

## Primeira publicação

1. Crie uma conta no [GitHub](https://github.com/) e ative a verificação em duas etapas.
2. Crie uma organização gratuita, como `ppgd-uenp`, e dentro dela um repositório público chamado `estante`.
3. Envie os arquivos desta pasta para o repositório.
4. Em **Settings > Pages**, escolha **GitHub Actions** como origem.
5. Na planilha, abra **Arquivo > Compartilhar > Publicar na Web**, escolha a aba **Livros** e o formato **CSV**. Copie o link gerado.
6. Cole o link em `scripts/fonte.json`, no campo `csv_url`.

Tudo que estiver nesse link fica público. Não coloque dados pessoais na planilha.

## Como transferir para o programa

### GitHub

1. Convide a conta institucional para a organização, como **Owner**, em **People**.
2. Com o convite aceito, confira se a conta institucional consegue abrir **Settings**.
3. Saia da organização, ou fique como membro comum. O endereço do site não muda.

### Planilha

1. Em **Compartilhar**, adicione a conta institucional como editora e tente passar a propriedade para ela.
2. Se o Google não permitir, porque a conta é de um domínio institucional, faça uma cópia dentro da conta nova.
3. Se a planilha tiver sido copiada, publique a cópia na Web e troque o link em `scripts/fonte.json`.

### Endereço oficial

Se a TI liberar um subdomínio da UENP, cadastre-o em **Settings > Pages > Custom domain** e peça à TI para apontar o endereço ao GitHub Pages. Depois, teste os links antigos.

## O que há nesta pasta

| Item | Função |
|---|---|
| `index.html` | A página do site |
| `dados/livros.json` | Os livros, gerados a partir da planilha |
| `capas/` | As imagens das capas |
| `scripts/atualizar_dados.py` | A rotina que lê a planilha |
| `scripts/fonte.json` | O link da planilha |
| `.github/workflows/publicar.yml` | O agendamento e a publicação |

Para ver o site no próprio computador, rode `python -m http.server` nesta pasta e abra `http://localhost:8000`. Abrir o `index.html` com dois cliques não funciona, porque o navegador bloqueia a leitura dos dados.
