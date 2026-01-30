# Guia Rápido - RuleField

## Instalação Rápida

1. **Importar o campo:**
```python
from django_rule_engine.fields import RuleField
```

2. **Adicionar ao modelo:**
```python
class MeuModelo(models.Model):
    regra = RuleField(
        verbose_name="Minha Regra",
        example_data={"idade": 25, "status": "ativo"}
    )
```

3. **Executar migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Verificar no admin:**
Registre seu modelo no admin e acesse. O editor aparecerá automaticamente!

## Uso no Admin

### Editando uma Regra

1. Abra o objeto no Django Admin
2. Digite a regra no editor (ex: `idade >= 18 and status == "ativo"`)
3. Ajuste o JSON de exemplo se necessário
4. Clique em **Validar** (ou pressione Ctrl+Enter)
5. Veja o resultado da validação
6. Salve o objeto

### Atalhos de Teclado

- **Ctrl+Enter** (Mac: Cmd+Enter): Validar regra
- JSON auto-formata ao colar

## Sintaxe Rápida

### Operadores

| Operador | Exemplo | Descrição |
|----------|---------|-----------|
| `==` | `status == "ativo"` | Igual a |
| `!=` | `tipo != "admin"` | Diferente de |
| `>` | `idade > 18` | Maior que |
| `>=` | `idade >= 18` | Maior ou igual |
| `<` | `preco < 100` | Menor que |
| `<=` | `preco <= 100` | Menor ou igual |
| `and` | `a and b` | E lógico |
| `or` | `a or b` | Ou lógico |
| `not` | `not ativo` | Não lógico |
| `in` | `"@edu.br" in email` | Contém |

### Exemplos Rápidos

```python
# Idade maior ou igual a 18
idade >= 18

# Status ativo E email institucional
status == "ativo" and "@ifrn.edu.br" in email

# Tipo premium OU compras acima de 5
tipo == "premium" or total_compras > 5

# Preço entre 50 e 200
preco >= 50 and preco <= 200

# Nome não vazio
len(nome) > 0

# Múltiplas condições
(idade >= 18 and idade <= 65) and (ativo == true or pendente == true)
```

## Uso Programático

```python
import rule_engine

# Obter objeto com regra
obj = MeuModelo.objects.get(pk=1)

# Compilar regra
regra = rule_engine.Rule(obj.regra)

# Testar com dados
dados = {"idade": 25, "status": "ativo"}
resultado = regra.matches(dados)  # True ou False

if resultado:
    print("Regra passou!")
else:
    print("Regra falhou!")
```

## Exemplos Práticos

### 1. Validação de Matrícula

```python
class Curso(models.Model):
    nome = models.CharField(max_length=200)
    regra_matricula = RuleField(
        example_data={
            "idade": 20,
            "nivel": "medio",
            "aprovado_vestibular": True
        }
    )

# Regra exemplo:
# idade >= 18 and nivel == "medio" and aprovado_vestibular == true
```

### 2. Desconto em Produtos

```python
class Promocao(models.Model):
    nome = models.CharField(max_length=200)
    regra_desconto = RuleField(
        example_data={
            "preco": 100.0,
            "quantidade": 3,
            "cliente_vip": False
        }
    )

# Regra exemplo:
# (quantidade >= 3 or cliente_vip == true) and preco > 50
```

### 3. Acesso a Recurso

```python
class Recurso(models.Model):
    nome = models.CharField(max_length=200)
    regra_acesso = RuleField(
        example_data={
            "usuario_admin": False,
            "departamento": "TI",
            "nivel_acesso": 5
        }
    )

# Regra exemplo:
# usuario_admin == true or (departamento == "TI" and nivel_acesso >= 3)
```

## Troubleshooting Rápido

### Erro: "Regra inválida"
- ✅ Verifique aspas em strings: `"texto"` ou `'texto'`
- ✅ Use `==` para comparação (não `=`)
- ✅ Variáveis devem existir no JSON de exemplo

### Widget não aparece
- ✅ Execute: `python manage.py collectstatic`
- ✅ Verifique se a URL da API está configurada

### Validação não funciona
- ✅ Verifique endpoint: `/api/validate-rule/`
- ✅ Verifique JSON de exemplo válido
- ✅ Olhe console do navegador para erros

## Links Úteis

- 📖 [Documentação Completa](./README.md)
- 📝 [Exemplos de Código](./examples.py)
- 🔗 [rule-engine Docs](https://zerosteiner.github.io/rule-engine/)

## Perguntas Frequentes

**P: Posso usar funções nas regras?**
R: Sim! Use `len()`, `abs()`, `max()`, `min()`, etc.

**P: Como testar strings?**
R: Use `in`: `"@edu.br" in email` ou `.startswith()`: `nome.startswith("João")`

**P: Posso ter múltiplos RuleFields?**
R: Sim! Cada campo é independente.

**P: Como validar no backend?**
R: Use `rule_engine.Rule(texto).matches(dados)`

**P: Funciona com NULL?**
R: Sim, use `blank=True, null=True` no campo.
