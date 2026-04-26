### TABELA DE REQUISITOS
| Componente       | Requisito Mínimo                                                                 |
|------------------|----------------------------------------------------------------------------------|
| Controlador      | Python 2.7+ (padrão em Linux)                                                    |
| Servidores Remotos | SSH habilitado, Python 2.7+ (opcional, mas recomendado para módulos sem agente) |
| Rede             | Acesso via SSH (porta 22) sem restrições de firewall                            |
| Autenticação     | Chave SSH ou senha configurada no controlador                                   |

---

### ANÁLISE DETALHADA: ansible (foco em integração)

#### Requisitos mínimos para controlar N servidores remotos?
- **Controlador**: Instalação do Ansible via gerenciador de pacotes (`yum`/`apt`) com Python pré-instalado.
- **Servidores Remotos**: SSH habilitado e acesso via chave SSH (sem agente). Python é opcional para módulos básicos, mas recomendado para funcionalidades avançadas.
- **Rede**: Conectividade direta na porta 22 entre controlador e servidores. Nenhuma instalação nos nós gerenciados.

#### Passo a passo para primeiro playbook funcional (instalar pacote + serviço)
1. **Instalar Ansible no controlador**:
   ```bash
   sudo apt update && sudo apt install -y ansible
   ```

2. **Criar arquivo de inventário** (`inventory.ini`):
   ```ini
   [servidores]
   servidor1 ansible_host=192.168.1.10
   servidor2 ansible_host=192.168.1.11
   ```

3. **Criar playbook** (`instala_apache.yml`):
   ```yaml
   ---
   - name: Instalar Apache e iniciar serviço
     hosts: servidores
     become: yes
     tasks:
       - name: Instalar Apache
         ansible.builtin.apt:
           name: apache2
           state: present
       - name: Iniciar serviço
         ansible.builtin.service:
           name: apache2
           state: started
           enabled: yes
   ```

4. **Executar playbook**:
   ```bash
   ansible-playbook -i inventory.ini instala_apache.yml
   ```

#### Como testar playbook sem aplicar mudanças reais?
- **Modo de simulação** (`--check`):
  ```bash
  ansible-playbook -i inventory.ini instala_apache.yml --check
  ```
- **Modo diff** (`--diff`):
  ```bash
  ansible-playbook -i inventory.ini instala_apache.yml --check --diff
  ```
- **Modo verboso** (`-v`):
  ```bash
  ansible-playbook -i inventory.ini instala_apache.yml -v
  ```

#### Erros mais comuns de SSH e inventário no primeiro uso?
1. **Falha de conexão SSH (Código 255)**:
   - **Causa**: Credenciais incorretas, chave SSH sem permissão 600, ou firewall bloqueando porta 22.
   - **Solução**: `chmod 600 ~/.ssh/id_rsa` e testar conexão manual com `ssh -i ~/.ssh/id_rsa usuario@servidor`.

2. **Erro de verificação de host key**:
   - **Causa**: Chave do servidor não está em `~/.ssh/known_hosts`.
   - **Solução**: Adicionar chave manualmente com `ssh-keyscan -H servidor >> ~/.ssh/known_hosts`.

3. **Inventário desatualizado**:
   - **Causa**: Hostnames ou IPs incorretos no arquivo `inventory.ini`.
   - **Solução**: Validar conectividade individual com `ansible all -i inventory.ini -m ping`.

---

### PRÓS
1. **Arquitetura sem agente**: Elimina a necessidade de instalar agentes nos servidores remotos, reduzindo complexidade e superfície de ataque.  
2. **Integração nativa com nuvem**: Plugins de inventário dinâmico para AWS, OpenStack e Azure, permitindo automação de infraestrutura como código.  
3. **Idempotência e testabilidade**: Modo `--check` simula alterações sem aplicar mudanças reais, garantindo segurança em ambientes críticos.

---

### CONTRAS
1. **Dependência de SSH**: Conexões instáveis em redes com alta latência ou restrições de firewall impactam a performance.  
2. **Curva de aprendizado para playbooks complexos**: Requer conhecimento de YAML, módulos e loops para automações avançadas.  
3. **Performance em larga escala**: Execução síncrona por padrão pode ser lenta para milhares de nós (solução: aumentar forks no `ansible.cfg`).

---

### OTIMIZAÇÕES
1. **Inventário dinâmico para AWS**:  
   ```bash
   ansible-inventory -i aws_ec2.yml --list
   ```
   Configuração em `aws_ec2.yml`:
   ```yaml
   plugin: aws_ec2
   regions:
     - us-east-1
   ```

2. **Paralelismo com forks**:  
   Adicionar em `ansible.cfg`:
   ```ini
   [defaults]
   forks = 50
   ```

3. **Tratamento de erros com `block`**:  
   ```yaml
   - name: Tarefa crítica
     block:
       - name: Instalar pacote
         apt:
           name: nginx
           state: present
     rescue:
       - name: Reverter em falha
         apt:
           name: nginx
           state: absent
   ```

---

### RECOMENDAÇÃO
Para automatizar configuração de servidores Linux sem agente com foco em integração, o Ansible é ideal devido à sua simplicidade, arquitetura baseada em SSH e suporte nativo a provedores de nuvem e ferramentas de CI/CD. Recomenda-se começar com playbooks básicos para instalação de pacotes e serviços, utilizando `--check` para validação prévia. Priorize a configuração de chaves SSH e inventários dinâmicos para escalabilidade, e integre com Terraform para provisionamento de infraestrutura unificado.