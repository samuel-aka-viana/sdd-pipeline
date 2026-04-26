# ansible
## URLS CONSULTADAS
https://phoenixnap.com/blog/ansible-alternatives  
https://www.guru99.com/ansible-alternative.html  
https://www.gurusoftware.com/the-complete-guide-on-robust-ansible-alternatives-for-modern-infrastructure-automation/  
https://github.com/ansible/ansible/issues/26269  
https://github.com/buluma/ansible-role-alternatives  
https://github.com/ansible/ansible-modules-extras/blob/devel/system/alternatives.py  
https://github.com/robertdebock/ansible-role-alternatives  
https://github.com/webarch-coop/ansible-role-alternatives  
https://dev.to/kuwv/why-i-use-ansible-over-docker-compose-edg  
https://medium.com/meetcyber/why-i-ditched-docker-compose-for-ansible-and-never-looked-back-8298919332ac  
https://www.techtarget.com/searchsoftwarequality/tip/Compare-Ansible-vs-Docker-use-cases-and-combinations  
https://cloudinfrastructureservices.co.uk/ansible-vs-docker-whats-the-difference-between-devops-tool/  
https://blog.purestorage.com/purely-educational/ansible-vs-docker/  
https://docs.ansible.com/projects/ansible/latest/collections/community/general/alternatives_module.html  
https://www.automq.com/blog/ansible-alternatives-2025-terraform-chef-salt-puppet-cfengine  
https://github.com/Traackr/ansible-elasticsearch  
https://github.com/ansible/ansible-ai-connect-service  
https://github.com/ansible-community/project-template/blob/main/COPYING  
https://github.com/ansible/product-demos  
https://github.com/punktDe/ansible-proserver-template  
https://docs.ansible.com/projects/ansible/latest/os_guide/intro_zos.html  
https://github.com/storedsafe/ansible-storedsafe  
https://www.elastic.co/docs/deploy-manage/deploy/cloud-enterprise/alternative-install-ece-with-ansible  
https://schneide.blog/tag/ansible/  
https://aws.amazon.com/blogs/desktop-and-application-streaming/announcing-the-amazon-workspaces-dynamic-inventory-plugin-for-ansible/  
https://www.deploymastery.com/2023/05/24/what-are-some-alternatives-to-ansible-exploring-options/  
https://www.iamgini.com/ansible-best-practices  
https://blog.cloudmylab.com/ansible-setup-step-by-step  
https://andidog.de/blog/2017-04-24-ansible-best-practices  
https://es.console-linux.com/?p=5217  
https://www.techsyncer.com/es/how-to-use-ansible-cheat-sheet-guide.html  
https://www.digitalocean.com/community/tutorials/como-usar-o-ansible-para-instalar-e-configurar-o-lemp-no-ubuntu-18-04-pt  
https://www.ediciones-eni.com/libro/ansible-administre-la-configuracion-de-sus-servidores-y-el-despliegue-de-sus-aplicaciones-9782409029783/uso-de-ansible  
https://cmdbox.mikihands.com/es/ansible/  
https://www.digitalocean.com/community/tutorials/configuration-management-101-writing-ansible-playbooks-pt  
https://infoslack.com/devops/automatize-o-gerenciamento-de-servidores-com-ansible  
https://www.tadeubernacchi.com.br/ansible-primeiros-passos-e-exemplos/  
https://labex.io/pt/tutorials/ansible-setting-up-an-ansible-lab-for-beginners-413785  
https://4linux.com.br/passo-passo-instalacao-ansible-debian-aws/  
https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_execution.html  
https://ansible-cbt-lab.readthedocs.io/en/latest/05_setting/03_testing.html  
https://www.geeksforgeeks.org/devops/dry-run-ansible-playbook/  
https://www.env0.com/blog/ansible-playbooks-step-by-step-guide  
https://computingforgeeks.com/ansible-debugging/  
https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/ssh_connection.html  
https://devops.aibit.im/pt/article/troubleshooting-ansible-ssh-connection-failures  
https://kx.cloudingenium.com/pt/ansible-playbook-troubleshooting-common-errors-debugging-pt/  
https://www.tutorialpedia.org/blog/ansible-ssh-prompt-known-hosts-issue/  
https://mindfulchase.com/explore/troubleshooting-tips/automation/advanced-ansible-troubleshooting-fixing-ssh-issues,-playbook-performance,-and-module-failures.html  
https://www.techblitz.ai/ansible-alternatives/  
https://www.guru99.com/ansible-tutorial.html  
https://www.env0.com/blog/the-ultimate-ansible-tutorial-a-step-by-step-guide  
https://www.whizlabs.com/blog/ansible-introduction/  
https://www.devopsschool.com/blog/the-complete-ansible-tutorial-concepts-architecture-playbooks-and-real-world-examples/  
https://docs.ansible.com/projects/ansible/latest/tips_tricks/sample_setup.html  
https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_plugins.html  
https://www.digitalocean.com/community/tutorials/configuration-management-101-writing-ansible-playbooks  
https://spacelift.io/blog/ansible-best-practices  
https://www.pluralsight.com/courses/getting-started-ansible  
https://attuneops.io/top-5-ansible-alternatives/  
https://spacelift.io/blog/ansible-alternatives  

## REQUISITOS DE HARDWARE
Sem dados concretos nos resultados. Os resultados indicam que o Ansible é leve e não tem restrições de hardware, podendo gerenciar milhares de nós sem requisitos específicos de sistema operacional ou hardware.

## COMANDOS DE INSTALAÇÃO
```bash
sudo yum install -y ansible
```
```bash
sudo apt update
sudo apt install ansible
```

## ERROS COMUNS
1. **Falha de conexão SSH**  
   - Causa: Credenciais incorretas, problemas com SSH agent ou restrições de rede.  
   - Solução: Verificar configurações de SSH e permissões de chaves.  

2. **Permissões incorretas de chave SSH**  
   - Causa: Ansible recusa conexões se a chave privada tiver permissões além de 0600.  
   - Solução: `chmod 600 key.pem`  

3. **Verificação de host key SSH**  
   - Causa: Erro "invalid argument" devido a configurações incorretas de verificação de host key ou control path.  
   - Solução: Verificar configurações de SSH host key.  

4. **Inventário desatualizado**  
   - Causa: Hostnames alterados no inventário causam falhas que parecem problemas de rede.  
   - Solução: Validar arquivo de inventário e hostnames.  

5. **Código de retorno SSH 255**  
   - Causa: Conflito entre código de erro de conexão SSH (255) e códigos de erro de comandos.  
   - Solução: Investigar tanto erros de conexão quanto de comandos.  

## DADOS RELEVANTES PARA: integração
- **Integração com provedores de nuvem**: Plugins de inventário dinâmico para AWS, OpenStack e outros.  
- **Integração com Terraform**: Provisionamento de infraestrutura com Terraform seguido de configuração com Ansible.  
- **Integração com Docker**: Gerenciamento de contêineres e orquestração via módulos Docker.  
- **Integração com Jenkins**: Automação de CI/CD usando playbooks em pipelines Jenkins.  
- **Integração com sistemas de segredos**: Uso do Ansible Vault para gerenciar credenciais.  

## ALTERNATIVAS MENCIONADAS
- Puppet  
- Chef  
- SaltStack  
- Terraform  
- CFEngine  
- Rudder  
- Docker Compose  
- Attune