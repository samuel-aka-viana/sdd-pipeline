# CONTEXTO BRUTO - ansible

- stats: {"discovered": 61, "ok": 11, "fail": 1, "snippet_fallback": 49, "skipped": 49}
- max_scrapes_per_tool: 12
- max_chars_per_scrape: 16000


### Busca: ansible alternatives integration example tutorial

### Busca: ansible alternatives end to end setup guide

### Busca: ansible alternatives getting started together
URL: https://phoenixnap.com/blog/ansible-alternatives
Resumo: This guide toAnsiblealternativesexplores 16 options that may be a better fit for different workloads, infrastructures, and environments.
---
URL: https://www.guru99.com/ansible-alternative.html
Resumo: As analternativetoAnsible, Rudder excels in bridging automation and compliance, its UI makes orchestration easier for teams, and its enforcement engine ensures drift is corrected automatically. Use it to manage infrastructure as code, enforce security baselines, and integrate with version control systems across cloud and on-prem environments.
---
URL: https://www.gurusoftware.com/the-complete-guide-on-robust-ansible-alternatives-for-modern-infrastructure-automation/
Resumo: In this comprehensive guide, we'll explore the most robustAnsiblealternativesavailable in 2025 with detailed analysis on critical considerations like scalability, architecture, cloud support, licensing, and ease of use.
---

### Busca: ansible connector alternatives site:github.com
URL: https://github.com/ansible/ansible/issues/26269
Resumo: June 30, 2017 -The ansible alternatives module doesn't support removing alternatives, it can only add or update them.
---
URL: https://github.com/buluma/ansible-role-alternatives
Resumo: --- - name: converge hosts: all become: true gather_facts: true roles: - role: buluma.alternatives · The machine needs to be prepared. In CI this is done using molecule/default/prepare.yml: --- - name: prepare hosts: all become: true gather_facts: false roles: - role: buluma.bootstrap tasks: - name: make a fake binary ansible.builtin.file: path: /bin/my_fake_binary state: touch mode: "0755" Also see a full explanation and example on how to use these roles.
---
URL: https://github.com/ansible/ansible-modules-extras/blob/devel/system/alternatives.py
Resumo: October 30, 2018 -Ansible module to manage symbolic link alternatives.
---
URL: https://github.com/robertdebock/ansible-role-alternatives
Resumo: --- - name: Converge hosts: all become: true gather_facts: true roles: - role: robertdebock.alternatives alternatives_list: - name: my_alternative_fake_binary link: /bin/my_alternative_fake_binary path: /bin/my_fake_binary · The machine needs to be prepared. In CI this is done using molecule/default/prepare.yml: --- - name: Prepare hosts: all become: true gather_facts: false roles: - role: robertdebock.bootstrap tasks: - name: Make a fake binary ansible.builtin.file: path: /bin/my_fake_binary state: touch mode: "0755" Also see a full explanation and example on how to use these roles.
---
URL: https://github.com/webarch-coop/ansible-role-alternatives
Resumo: An Ansible role to manage Debian and Ubuntu alternatives - webarch-coop/ansible-role-alternatives
---

### Busca: ansible alternatives docker compose example
URL: https://dev.to/kuwv/why-i-use-ansible-over-docker-compose-edg
Resumo: December 30, 2024 -Setting up docker resources is relatively the same. Both docker-compose and Ansible can setup resources such as networks and volumes within Docker. The YAML used by both systems are relatively similar. Example docker-compose for building resources from jerney.io:
---
URL: https://medium.com/meetcyber/why-i-ditched-docker-compose-for-ansible-and-never-looked-back-8298919332ac
Resumo: June 19, 2025 -You guessed it — Docker Compose. But somewhere along the way, I hit a wall. Not a technical wall, but a philosophical one. I realized I was thinking too narrowly about orchestration, treating containers as the center of my universe when they should have been just one piece of a much larger puzzle. This is the story of why I made the switch to Ansible for container orchestration, and why I believe it might be the right choice for you too.
---
URL: https://www.techtarget.com/searchsoftwarequality/tip/Compare-Ansible-vs-Docker-use-cases-and-combinations
Resumo: November 19, 2024 -Ansible and Docker play specific roles, but when used together, Ansible's playbooks and Docker's Dockerfiles provide greater control and configurability over servers. ... What is a Docker container vs. an image? – Search IT Operations · Dockerfile vs docker-compose: What's the difference?
---
URL: https://cloudinfrastructureservices.co.uk/ansible-vs-docker-whats-the-difference-between-devops-tool/
Resumo: September 3, 2022 -In essence Ansible manages the entire environment together with the applications or containers. Therefore, you don’t have to worry about provisioning the underlying environment. Docker, on the other hand, manages the underlying application partially. It manages only the assigned environment. Therefore, users should be careful of the containerized environment. ... For example Ansible is written in Python programming language.
---
URL: https://blog.purestorage.com/purely-educational/ansible-vs-docker/
Resumo: November 11, 2025 -The Docker ecosystem is rich with tools and extensions that extend its functionality and adapt it to various use cases. Docker Compose, for example, simplifies the management of multi-container applications, whileDocker Swarmenables orchestration ...
---

### Busca: ansible alternatives architecture diagram how they fit
URL: https://docs.ansible.com/projects/ansible/latest/collections/community/general/alternatives_module.html
Resumo: ControllinghowAnsiblebehaves: precedence rules. YAML Syntax.community.general.alternativesmodule – Managesalternativeprograms for common commands. Note. This module is part of the community.general collection (version 12.5.0).
---
URL: https://www.automq.com/blog/ansible-alternatives-2025-terraform-chef-salt-puppet-cfengine
Resumo: Discover leadingalternativestoAnsiblefor 2025, exploring Puppet, Chef, SaltStack, Terraform, and CFEngine to boost your DevOps toolkit's efficiency.Design andHowIt Works: Salt operates on a master-minionarchitecturebut also supports agentless execution via Salt SSH.
---

### Busca: ansible alternatives example project site:github.com
URL: https://github.com/Traackr/ansible-elasticsearch
Resumo: After installing Vagrant, run vagrant up at the root of theprojectto get an VM instance bootstrapped and configured with a running instance of ...
---
URL: https://github.com/ansible/ansible-ai-connect-service
Resumo: DEPLOYMENT_MODE= " upstream " SECRET_KEY= " somesecretvalue " WCA_SECRET_BACKEND_TYPE= " dummy " configure model serverANSIBLE_AI_MODEL_MESH_CONFIG ...
---
URL: https://github.com/ansible-community/project-template/blob/main/COPYING
Resumo: ansible-community /project-template Public template ... Forexample, if you distribute copies of such a program, whether
---
URL: https://github.com/ansible/product-demos
Resumo: TheAnsibleProduct Demos (APD)projectis a set ofAnsibledemos that run on the Red HatAnsibleAutomation Platform (AAP).
---
URL: https://github.com/punktDe/ansible-proserver-template
Resumo: Thisexampleplaybook demonstrates the use of our publicly availableAnsibleroles for the proServer. ...Ansibleplaybookexamplesfor your ...
---

### Busca: ansible exporter plugin alternatives
URL: https://docs.ansible.com/projects/ansible/latest/os_guide/intro_zos.html
Resumo: Alternatively, consider using theansible.builtin.command oransible.builtin.shell modules mentioned above, which set up the configured remote ...
---
URL: https://github.com/storedsafe/ansible-storedsafe
Resumo: The source for theplugincan be pointed to via a requirements.yml file, and accessed viaansible-galaxy . ...ansible-vault lookup module, which has ...
---
URL: https://www.elastic.co/docs/deploy-manage/deploy/cloud-enterprise/alternative-install-ece-with-ansible
Resumo: If you already useAnsiblein your business for provisioning, configuration management, and application deployment, you can use the ECEAnsible...
---
URL: https://schneide.blog/tag/ansible/
Resumo: All the tinkering with the jenkinsansiblepluginis unnecessary going this way and relying on docker and what the container provides for running ...
---
URL: https://aws.amazon.com/blogs/desktop-and-application-streaming/announcing-the-amazon-workspaces-dynamic-inventory-plugin-for-ansible/
Resumo: ... inventorypluginforAnsible. ... In order to help with these tasks, I am announcing an Amazon WorkSpaces dynamic inventorypluginforAnsible.
---

### Busca: ansible alternatives common integration errors
URL: https://www.deploymastery.com/2023/05/24/what-are-some-alternatives-to-ansible-exploring-options/
Resumo: Ansiblehas long been a popular choice for automating infrastructure provisioning, configuration management, and application deployment. However, the rapidly evolving landscape of DevOps tools offers a variety ofalternativesthat can be worth considering. In this post, we will explore some noteworthyalternativestoAnsible, highlighting their key features, benefits, and use cases. Whether ...
---

### Busca: ansible alternatives production setup best practices
URL: https://www.iamgini.com/ansible-best-practices
Resumo: Note : This document is somewhat based on original document -BestPractices- and I am keeping a modified copy with more details for my own ...
---
URL: https://blog.cloudmylab.com/ansible-setup-step-by-step
Resumo: This guide provides an in-depth explanation ofAnsible’s key concepts, installation, andbestpracticesto help network engineers confidently ...
---
URL: https://andidog.de/blog/2017-04-24-ansible-best-practices
Resumo: If you don ’ t have staging, you should probably aim at automating stagingsetupwithAnsible, since you already develop theproduction...
---

### Busca: ansible requisitos nimos controlar servidores remotos
URL: https://es.console-linux.com/?p=5217
Resumo: Ansiblees una herramienta de administración de configuración que está diseñada para automatizar el control deservidorespara administradores y equipos de operaciones. ConAnsible, puede usar un únicoservidorcentral paracontrolary configurar muchos sistemasremotosdiferentes...
---
URL: https://www.techsyncer.com/es/how-to-use-ansible-cheat-sheet-guide.html
Resumo: IntroducciónAnsiblees una herramienta moderna de gestión de configuraciones que facilita la tarea de configurar y mantenerservidoresremotos.
---
URL: https://www.digitalocean.com/community/tutorials/como-usar-o-ansible-para-instalar-e-configurar-o-lemp-no-ubuntu-18-04-pt
Resumo: Um node decontroleAnsible: uma máquina Ubuntu 18.04 com oAnsibleinstalado e configurado para conectar aos seus hostsAnsibleusando chaves SSH.
---
URL: https://www.ediciones-eni.com/libro/ansible-administre-la-configuracion-de-sus-servidores-y-el-despliegue-de-sus-aplicaciones-9782409029783/uso-de-ansible
Resumo: Uso deAnsible. Objetivo del capítulo yrequisitos.Ansibleya está instalado y susservidoresestán preparados para aceptar conexiones SSH con el sistema de claves. Ahora es el momento de empezar a administrar sus máquinas. 1. Contexto yrequisitos.
---
URL: https://cmdbox.mikihands.com/es/ansible/
Resumo: Descripción general.Ansibleopera de forma sin agentes (agentless), lo que significa que no es necesario instalar software adicional en losservidoresgestionados. Ejecuta comandos a través de conexiones SSH y utiliza módulos escritos en Python para realizar diversas tareas.
---

### Busca: ansible passo passo primeiro playbook funcional instalar pacote servi
URL: https://www.digitalocean.com/community/tutorials/configuration-management-101-writing-ansible-playbooks-pt
Resumo: February 20, 2020 -Control Node: a máquina em que o Ansible está instalado, responsável pela execução do provisionamento nos servidores que você está gerenciando. Inventory: um arquivo INI que contém informações sobre os servidores que você está gerenciando. Playbook: um arquivo YAML contendo uma série de procedimentos que devem ser automatizados. Task: um bloco que define um único procedimento a ser executado, por exemplo: instalar um pacote.
---
URL: https://infoslack.com/devops/automatize-o-gerenciamento-de-servidores-com-ansible
Resumo: O último comando na linha 9 é o apt: que recebe como parâmetro o nome do pacote que queremos instalar name=nginx e outro argumento update_cache=yes que seria o mesmo queapt-get update && apt-get install nginx. E para executar nosso playbook, precisamos escrever mais um arquivo, chamado ...
---
URL: https://www.tadeubernacchi.com.br/ansible-primeiros-passos-e-exemplos/
Resumo: May 4, 2017 -[root@notebook ansible]# ansible all --list-hosts --ask-vault-pass Vault password: hosts (3): ansible2 ansible3 ansible4 ... Para ilustrar a praticidade e simplicidade de funcionamento do Ansible vamos criar um playbook de exemplo para desabilitar o SeLinux, remover o Firewalld, ajustar o timezone, o idioma, o teclado, e instalar e configurar o NTP em servidores CentOS7.
---
URL: https://labex.io/pt/tutorials/ansible-setting-up-an-ansible-lab-for-beginners-413785
Resumo: - hosts: webservers tasks: - name: Instalar Apache apt: name: apache2 state: present - name: Iniciar o serviço Apache service: name: apache2 state: started enabled: true ...Instalar o pacote do servidor web Apache.
---
URL: https://4linux.com.br/passo-passo-instalacao-ansible-debian-aws/
Resumo: August 30, 2024 -Você precisarágerar uma chave SSH para cada servidor e adicioná-la ao arquivo de chaves do servidor Ansible controlador. O Ansible controlador deve ter o Python 2.7 ou superior instalado.
---

### Busca: ansible testar playbook aplicar mudan reais
URL: https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_execution.html
Resumo: You can validate your tasks with "dry run"playbooks, use the start-at-task and step mode options to efficiently troubleshootplaybooks. You can also useAnsibledebugger to correct tasks during execution.Ansiblealso offers flexibility with asynchronousplaybookexecution and tags that let you run specific parts of yourplaybook.
---
URL: https://ansible-cbt-lab.readthedocs.io/en/latest/05_setting/03_testing.html
Resumo: This command tellsAnsibleto execute theplaybook(playbook.yml) using your inventory file. Creating and running a simpleAnsibleplaybookis a powerful way to automate tasks on network devices. This basicplaybookgathers facts from an IOS device and displays them, providing a foundation you can build on for more complex automation workflows.
---
URL: https://www.geeksforgeeks.org/devops/dry-run-ansible-playbook/
Resumo: This article described the core ideas and key terms inAnsibledry runs, presenting the step-by-step process of realplaybookexecution in check mode. Following best practices and guidelines, one can safely test automation tasks and configurations to assure flawless deployments without any errors.
---
URL: https://www.env0.com/blog/ansible-playbooks-step-by-step-guide
Resumo: Unlike one-off ad-hoc commands,playbooksare repeatable, version-controlled, and human-readable. They are the standard way to express automation withAnsible. This guide coversAnsibleplaybooksyntax, how to write and run your firstplaybook, how to use tags, and a complete real-world deployment example with Apache, Flask, and PostgreSQL.
---
URL: https://computingforgeeks.com/ansible-debugging/
Resumo: DebugAnsibleplaybookswith -vvvv, check mode, --start-at-task,ansible-inventory, defensive asserts, and a real undefined-variable walkthrough on Rocky 10.
---

### Busca: ansible erros mais comuns ssh invent rio primeiro uso
URL: https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/ssh_connection.html
Resumo: 5 days ago ·ThesshCLI tool uses return code 255 as a ‘connectionerror’, this can conflict with commands/tools that also return 255 as anerrorcode and will look like an ‘unreachable’ condition or ‘connectionerror’ to this plugin.
---
URL: https://devops.aibit.im/pt/article/troubleshooting-ansible-ssh-connection-failures
Resumo: Nov 3, 2025 ·Este guia fornece uma metodologia passo a passo para diagnosticar e resolver asfalhasde conexãoSSHmaiscomunsencontradas ao executar playbooksAnsible, garantindo que o gerenciamento de sua configuração funcione sem problemas.
---
URL: https://kx.cloudingenium.com/pt/ansible-playbook-troubleshooting-common-errors-debugging-pt/
Resumo: Corrijaerroscomunsem playbooksAnsibleincluindo timeoutsSSH, escalação de privilégios, variáveis indefinidas e idempotência passo a passo.
---
URL: https://www.tutorialpedia.org/blog/ansible-ssh-prompt-known-hosts-issue/
Resumo: Jan 16, 2026 ·In some cases, this manifests as an "invalid argument"error, often tied to misconfigurations inSSHhost key checking or control path settings. In this blog, we’ll demystify the root causes of thiserrorand provide step-by-step solutions to resolve it.
---
URL: https://mindfulchase.com/explore/troubleshooting-tips/automation/advanced-ansible-troubleshooting-fixing-ssh-issues,-playbook-performance,-and-module-failures.html
Resumo: One of the mostcommonissuesinAnsibleisSSHconnection failures, often caused by incorrect credentials,SSHagent issues, or network restrictions. Solution: Verify SSH configurations and permissions.
---
URL: https://www.techblitz.ai/ansible-alternatives/
Conteúdo Extraído:
![](https://l.cdn-fileserver.com/bping.php?r=1777226531495&vgd_cage=4&vgd_oreqf=one&crid=710956738&cc=BR&vgd_asn=266630&vgd_wlstp=0&prid=8PR11258V&cid=8CURIXDH0&lf=6&mspa=0&vgd_cdv=O3125&vgd_oresf=one&vgd_setup=c21&vi=1777226531163858144&lper=100&wsip=170762499&requrl=https%3A%2F%2Ftechblitz.ai%2Fansible-alternatives%2F&ssld=%7B%22QQNN%22%3A%22RD%22%2C%22QQN75%22%3A%22Y1z1xQ%22%2C%22QQ8E%22%3A%22%22%2C%22QQQN%22%3A%22Kc%22%2C%22QQl8E%22%3A%22%22%7D&wshp=0&vgd_tsce=L1211&vgd_l2type=dmola&hvsid=00001777226531494021606919683481&ugd=4&sc=AM&vgd_rpth=%2Fola&gdpr=0&vgd_len=581&vgd_end=1)

---
URL: https://www.guru99.com/ansible-tutorial.html [TRUNCADO]
Conteúdo Extraído:
is an open source automation and orchestration tool for software provisioning, configuration management, and software deployment. Ansible can easily run and configure Unix-like systems as well as Windows systems to provide infrastructure as code. It contains its own declarative programming language for system configuration and management.
Ansible is popular for its simplicity of installation, ease of use in what concerns the connectivity to clients, its lack of agent for Ansible clients and the multitude of skills. It functions by connecting via to the clients, so it doesn’t need a special agent on the client-side, and by pushing modules to the clients, the modules are then executed locally on the client-side and the output is pushed back to the Ansible server.
Since it uses SSH, it can very easily connect to clients using SSH-Keys, simplifying though the whole process. Client details, like hostnames or IP addresses and SSH ports, are stored in files called inventory files. Once you have created an inventory file and populated it, ansible can use it.
Here are some important pros/benefits of using Ansible
  * One of the most significant advantages of Ansible is that it is free to use by everyone.
  * It does not need any special system administrator skills to install and use Ansible, and the official documentation is very comprehensive.
  * Its modularity regarding plugins, modules, inventories, and playbooks make Ansible the perfect companion to orchestrate large environments.
  * Ansible is very lightweight and consistent, and no constraints regarding the operating system or underlying hardware are present.
  * It is also very secure due to its agentless capabilities and due to the use of OpenSSH security features.
  * Another advantage that encourages the adoption of Ansible is its smooth learning curve determined by the comprehensive documentation and easy to learn structure and configuration.


Here, are important land marks from the history of ansible:
  * In February 2012 the Ansible project began. It was first developed by Michael DeHaan, the creator of Cobbler and Func, Fedora Unified Network Controller.
  * Initially called AnsibleWorks Inc, the company funding the ansible tool was acquired in 2015 by RedHat and later on, along with RedHat, moved under the umbrella of IBM.
  * In the present, Ansible comes included in distributions like Fedora Linux, RHEL, Centos and Oracle Linux.


  * The machine where Ansible is installed and from which all tasks and playbooks will be ran
  * Basically, a module is a command or set of similar Ansible commands meant to be executed on the client-side
  * A task is a section that consists of a single procedure to be completed
  * A way of organizing tasks and related files to be later called in a playbook
  * Information fetched from the client system from the global variables with the gather-facts operation
  * File containing data about the ansible client servers. Defined in later examples as hosts file
  * Task which is called only if a notifier is present
  * Section attributed to a task which calls a handler if the output is changed
  * Name set to a task which can be used later on to issue just that specific task or group of tasks.


  * Nagios Tutorial: What is Nagios Tool? Architecture & Installation 


Once you have compared and weighed your options and decided to go for Ansible, the next step is to have it installed on your system. We will go through the steps of installation in different distributions, the most popular ones, in the next small tutorial.

```
[root@ansible-server ~]# sudo  yum install -y ansible

```

```
$ sudo apt update
$ sudo apt install ansible

```

One of the simplest ways Ansible can be used is by using ad-hoc commands. These can be used when you want to issue some commands on a server or a bunch of servers. Ad-hoc commands are not stored for future uses but represent a fast way to interact with the desired servers.
For this Ansible tutorial, a simple two servers hosts file will be configured, containing host1 and host2.
You can make sure that the hosts are accessible from the ansible server by issuing a ping command on all hosts.

```
[root@ansible-server test_ansible]# ansible -i hosts all -m ping
host1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
host2 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}

```

  1. Status of the command, in this case, SUCCESS
  2. The command issued via the -m parameter, in this case, ping
  3. With the -i parameter, you can point to the hosts file.

You can issue the same command only on a specific host if needed.
```
[root@ansible-server test_ansible]# ansible -i hosts all -m ping --limit host2
host2 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}

```

  1. Limit parameter can be used to issue commands only on specific hosts in the host’s file
  2. Name of the host as defined in the inventory file


If you need to copy a file to multiple destinations rapidly, you can use the copy module in ansible which uses SCP. So the command and its output look like below:

```
[root@ansible-server test_ansible]# ansible -i hosts all -m copy -a "src=/root/test_ansible/testfile dest=/tmp/testfile"
host1 | SUCCESS => {
    "changed": true,
    "checksum": "da39a3ee5e6b4b0d3255bfef95601890afd80709",
    "dest": "/tmp/testfile",
    "gid": 0,
    "group": "root",
    "md5sum": "d41d8cd98f00b204e9800998ecf8427e",
    "mode": "0644",
    "owner": "root",
    "size": 0,
    "src": "/root/.ansible/tmp/ansible-tmp-1562216392.43-256741011164877/source",
    "state": "file",
    "uid": 0
}
host2 | SUCCESS => {
    "changed": true,
    "checksum": "da39a3ee5e6b4b0d3255bfef95601890afd80709",
    "dest": "/tmp/testfile",
    "gid": 0,
    "group": "root",
    "md5sum": "d41d8cd98f00b204e9800998ecf8427e",
    "mode": "0644",
    "owner": "root",
    "size": 0,
    "src": "/root/.ansible/tmp/ansible-tmp-1562216392.6-280302911361278/source",
    "state": "file",
    "uid": 0
}

```

  1. Module arguments, in this case, are source absolute path and destination absolute path.
  2. Ansible command output reflecting the success of the copy command and other details like the sha1 or md5 checksums for file integrity check and metadata like owner, size, or permissions.It is effortless to have a package installed on a bunch of servers. Ansible has several modules that interact with used installers, like yum, apt, dnf, etc.


In the next example, you will find out how to install a package via the yum module on two Centos hosts.

```
[root@ansible-server test_ansible]# ansible -i hosts all -m yum -a 'name=ncdu state=present'
host1 | SUCCESS => {
    "changed": true,
    "msg": "",
    "rc": 0,
    "results": [


"Loaded plugins: fastestmirror\nLoading mirror speeds from cached hostfile\n * base: mirror.netsite.dk\n * elrepo: mirrors.xservers.ro\n * epel: fedora.mirrors.telekom.ro\n * extras: centos.mirrors.telekom.ro\n * remi-php70: remi.schlundtech.de\n * remi-safe: remi.schlundtech.de\n * updates: centos.mirror.iphh.net\nResolving Dependencies\n--> Running transaction check\n---> Package ncdu.x86_64 0:1.14-1.el7 will be installed\n--> Finished Dependency Resolution\n\nDependencies Resolved\n\n================================================================================\n Package         Arch              Version                Repository       Size\n================================================================================\nInstalling:\n ncdu            x86_64            1.14-1.el7             epel             51 k\n\nTransaction Summary\n================================================================================\nInstall  1 Package\n\nTotal download size: 51 k\nInstalled size: 87 k\nDownloading packages:\nRunning transaction check\nRunning transaction test\nTransaction test succeeded\nRunning transaction\n  Installing : ncdu-1.14-1.el7.x86_64                                       1/1 \n  Verifying  : ncdu-1.14-1.el7.x86_64                                       1/1 \n\nInstalled:\n  ncdu.x86_64 0:1.14-1.el7                                                      \n\nComplete!\n"
    ]
}
host2 | SUCCESS => {
    "changed": true,
    "msg": "",
    "rc": 0,
    "results": [
        "Loaded plugins: fastestmirror\nLoading mirror speeds from cached hostfile\n * base: mirror.netsite.dk\n * elrepo: mirrors.leadhosts.com\n * epel: mirrors.nav.ro\n * extras: centos.mirrors.telekom.ro\n * remi-php70: mirrors.uni-ruse.bg\n * remi-safe: mirrors.uni-ruse.bg\n * updates: centos.mirror.iphh.net\nResolving Dependencies\n--> Running transaction check\n---> Package ncdu.x86_64 0:1.14-1.el7 will be installed\n--> Finished Dependency Resolution\n\nDependencies Resolved\n\n================================================================================\n Package         Arch              Version                Repository       Size\n================================================================================\nInstalling:\n ncdu            x86_64            1.14-1.el7             epel             51 k\n\nTransaction Summary\n================================================================================\nInstall  1 Package\n\nTotal download size: 51 k\nInstalled size: 87 k\nDownloading packages:\nRunning transaction check\nRunning transaction test\nTransaction test succeeded\nRunning transaction\n  Installing : ncdu-1.14-1.el7.x86_64                                       1/1 \n  Verifying  : ncdu-1.14-1.el7.x86_64                                       1/1 \n\nInstalled:\n  ncdu.x86_64 0:1.14-1.el7                                                      \n\nComplete!\n"
    ]
}

```

  1. It defines the module arguments, and in this case, you will choose the name of the package and its state. If the state is absent, for example, the package will be searched and if found, removed
  2. When colored in yellow, you will see the output of the ansible command with the state changed, meaning in this case, that the package was found and installed.
  3. Status of the yum install command issued via ansible. In this case the package ncdu.x86_64 0:1.14-1.el7 was installed.


Of course, all of the yum installer options can be used via ansible, including update, install, latest version, or remove.
In the below example the same command was issued to remove the previously installed ncdu package.

```
[root@ansible-server test_ansible]# ansible -i hosts all -m yum -a 'name=ncdu state=absent'
host1 | SUCCESS => {
    "changed": true,
    "msg": "",
    "rc": 0,
    "results": [
        "Loaded plugins: fastestmirror\nResolving Dependencies\n--> Running transaction check\n---> Package ncdu.x86_64 0:1.14-1.el7 will be erased\n--> Finished Dependency Resolution\n\nDependencies Resolved\n\n================================================================================\n Package         Arch              Version               Repository        Size\n================================================================================\nRemoving:\n ncdu            x86_64            1.14-1.el7            @epel             87 k\n\nTransaction Summary\n================================================================================\nRemove  1 Package\n\nInstalled size: 87 k\nDownloading packages:\nRunning transaction check\nRunning transaction test\nTransaction test succeeded\nRunning transaction\n  Erasing    : ncdu-1.14-1.el7.x86_64                                       1/1 \n  Verifying  : ncdu-1.14-1.el7.x86_64                                       1/1 \n\nRemoved:\n  ncdu.x86_64 0:1.14-1.el7                                                      \n\nComplete!\n"
    ]
}
host2 | SUCCESS => {
    "changed": true,
    "msg": "",
    "rc": 0,
    "results": [
        "Loaded plugins: fastestmirror\nResolving Dependencies\n--> Running transaction check\n---> Package ncdu.x86_64 0:1.14-1.el7 will be erased\n--> Finished Dependency Resolution\n\nDependencies Resolved\n\n================================================================================\n Package         Arch              Version               Repository        Size\n================================================================================\nRemoving:\n ncdu            x86_64            1.14-1.el7            @epel             87 k\n\nTransaction Summary\n================================================================================\nRemove  1 Package\n\nInstalled size: 87 k\nDownloading packages:\nRunning transaction check\nRunning transaction test\nTransaction test succeeded\nRunning transaction\n  Erasing    : ncdu-1.14-1.el7.x86_64                                       1/1 \n  Verifying  : ncdu-1.14-1.el7.x86_64                                       1/1 \n\nRemoved:\n  ncdu.x86_64 0:1.14-1.el7                                                      \n\nComplete!\n"
    ]
}

```

  1. The output of the yum command shows that the package was removed.


Another useful and essential feature that ansible uses to interact with the client’s server is to gather some facts about the system. So, it fetches hardware, software, and versioning information from the system and stores each value in a variable that can be later on used.
If you need detailed information about the systems to be modified via ansible, the next command can be used. The setup module gathers facts from the system variables.
are the way of sending commands to remote systems through scripts. Ansible playbooks are used to configure complex system environments to increase flexibility by executing a script to one or more systems. Ansible playbooks tend to be more of a configuration language than a programming language.
Ansible playbook commands use YAML format, so there is not much syntax needed, but indentation must be respected. Like the name is saying, a playbook is a collection of plays. Through a playbook, you can designate specific roles to some hosts and other roles to other hosts. By doing so, you can orchestrate multiple servers in very diverse scenarios, all in one playbook.
To have all the details precise before continuing with Ansible playbook examples, we must first define a task. These are the interface to ansible modules for roles and playbooks.
Now, let’s learn Ansible playbook through an example with one playbook with one play, containing multiple tasks as below:

```
---

- hosts: group1
  tasks:
  - name: Install lldpad package
    yum:
      name: lldpad
      state: latest
  - name: check lldpad service status
    service:
      name: lldpad
      state: started

```

In the above Ansible playbook example, the group1 of hosts in the host’s file is targeted for lldpad package installation using the yum module and afterward the service lldpad created after the installation is then started using the service module used mostly to interact with systemd ensemble.
  1. Group of hosts on which the playbook will run
  2. Yum module is used in this task for lldpad installation
  3. The service module is used to check if the service is up and running after installation


Each ansible playbook works with an inventory file. The inventory file contains a list of servers divided into groups for better control for details like and SSH port for each host.
The inventory file you can use for this Ansible playbook example looks like below. There are two groups, named group1 and group2 each containing host1 and host2 respectively.
  1. Hostname, with IP address and ssh port, in this case, the default one, 22.


Another useful Ansible playbook example containing this time two plays for two hosts is the next one. For the first group of hosts, group1, selinux will be enabled. If it is enabled, then a message will appear on the screen of the host.
For the second group of hosts, httpd package will be installed only if the ansible_os_family is RedHat and ansible_system_vendor is HP.
Ansible_os_family and ansible_system_vendor are variables gathered with gather_facts option and can be used like in this conditiona
---
URL: https://www.env0.com/blog/the-ultimate-ansible-tutorial-a-step-by-step-guide [TRUNCADO]
Conteúdo Extraído:
Manual server configuration is reproducible in theory and chaotic in practice. Every engineer has a slightly different mental model of what is installed, what version, and what is configured. Ansible fixes this: describe the desired state once in a YAML file and Ansible applies it to every machine in your inventory over SSH.
This is the hands-on beginner guide to Ansible: what it is, how to install it, how to write and run your first playbook, and how to scale from one server to hundreds. If you already know Ansible basics and want the technical reference, the covers YAML syntax, handlers, variables, and tags in depth.
> Ansible is an agentless automation platform that connects to managed nodes over SSH. Current stable release: (March 2026). Playbooks are YAML files that describe the desired state of your infrastructure: no agent software required on managed nodes. env zero wraps Ansible playbooks with team workflows, role-based access control (RBAC), and audit logs without modifying your YAML.


Ansible is an open-source automation platform built for configuration management, application deployment, and orchestration. Its agentless architecture, YAML-based playbooks, and ability to manage thousands of nodes over SSH have made it the default choice for DevOps teams that need repeatable, auditable infrastructure automation.
In this tutorial, we cover the fundamentals from installation to creating your first playbook. Later sections include practical hands-on examples for advanced use cases, with a full Jenkins CI/CD demo showing Ansible and Terraform working together.
Ansible's appeal starts with its architecture. It connects to managed nodes over SSH and pushes small programs called modules to perform specific tasks. Nothing is installed on those nodes: no agent, no daemon, no persistent process. That means you can apply Ansible to existing infrastructure immediately, without a migration project first.
Playbooks are written in YAML, the same format used by Docker Compose, Kubernetes manifests, and GitHub Actions. Teams already familiar with any of those formats can read and review Ansible playbooks without learning new syntax. That legibility matters during security audits and code reviews, when someone who did not write the automation needs to verify what it actually does.
Idempotency is the feature that makes Ansible safe to run repeatedly. When a task already finds the system in its desired state, subsequent runs make no changes; they confirm the state is correct. Run the same playbook in a CI/CD pipeline on every deployment and it verifies correctness without triggering unnecessary service restarts.
> Ansible vs Terraform: Choose One or Use Both? Ansible handles configuration and application deployment; Terraform handles infrastructure provisioning. Most mature teams use both.
Here is what each core component does and how they connect:
: A system on which Ansible is installed. You run Ansible commands such as on a control node.
The inventory is created on the control node to define the hosts for Ansible to manage and deploy.
A remote system, or host, that Ansible controls.
  * An inventory is a list of hosts/nodes with IP addresses or hostnames.
  * The default location for inventory is , but you can define a custom one in any directory.
  * You can configure inventory parameters per host, such as host, user, and SSH connection parameters.


Modules are the units of work in Ansible. Each one does exactly one thing: installs packages on Debian systems, manages user accounts, transfers files to remote hosts. There are thousands of built-in modules covering nearly every system administration task. They are grouped into collections, and you can add third-party collections with .
Plugins extend Ansible's core behavior. Connection plugins control how Ansible reaches hosts: SSH is the default, but WinRM handles Windows targets and runs tasks directly on the control node. Callback plugins format and route task output. Filter plugins transform data inside Jinja2 templates. Most users never write a custom plugin, but understanding they exist explains why Ansible handles scenarios no built-in module covers directly. See the for the full list.
A playbook is a YAML file containing one or more plays. Each play targets a set of hosts and runs a list of tasks in order. When you run , Ansible reads the file top to bottom, connects to each targeted host over SSH, and applies every task in sequence. If a task fails, execution stops for that host unless you configure error handling with or a block.
Here is a minimal working playbook using fully qualified collection names (FQCN), the recommended best practice since Ansible 2.10:
The prefix is the FQCN. It removes ambiguity when multiple collections define modules with the same short name. The directive runs tasks with elevated privileges, the equivalent of .
> Ansible Playbook Guide: Syntax, Examples & Best Practices. Covers handlers, variables, roles, and tags in depth: the natural next step after this tutorial.
A play binds a set of hosts to a set of tasks. One playbook can contain multiple plays, each targeting different host groups and defining its own and roles. That's how you'd write a single playbook that first configures database servers, then web servers, with distinct task sets for each.
Roles bundle reusable content like tasks, handlers, and variables for use within a Play.
Tasks specify actions to execute on managed hosts. They can be run individually using ad hoc commands.
Handlers are special tasks triggered only when notified by a previous task that has made a change.
Ansible Vault encrypts sensitive values, such as passwords, API keys, and certificates, so they can be committed to version control without exposing secrets. Encrypt a variable file with and Ansible decrypts it at runtime when you pass or point to a vault password file. Most teams use Vault for local development and move to a secrets manager such as AWS Secrets Manager or HashiCorp Vault for CI/CD pipelines. Any production playbook that touches credentials should use Vault or an equivalent.
Without roles, playbooks grow into monoliths: hundreds of tasks in a single file, logic duplicated across projects, nothing anyone wants to modify. Roles fix this by organizing automation into a standard directory layout, with separate folders for tasks, handlers, templates, and variable defaults. Each role is self-contained and portable across environments.
Roles simplify playbook management by breaking a large playbook into self-contained directories, each with their own tasks, handlers, templates, and variable defaults. Create a new role skeleton with , then reference it from your playbook under a key. This is how production Ansible environments are structured: one role per service, one playbook that composes them.
> Ansible Playbook Guide: Syntax, Variables, Roles, and Tags. A full deep-dive on roles, handlers, and variables with working examples.
Most Ansible problems fall into a small set of repeating patterns. Knowing them before you hit them saves hours of debugging.
Run before your first playbook run. Ansible refuses connections if the private key file has permissions broader than . This is the most common first-run failure by a wide margin.
If a task that installs packages or writes to system directories fails with a permission error, check before looking anywhere else. It's almost always that.
The and modules run unconditionally, every time, regardless of whether anything has changed. That's fine for one-off operations, but it breaks the "run it a hundred times, get the same result" property that makes Ansible safe in pipelines. Use a purpose-built module when one exists. When you have to use , add (skip if this file already exists) or to make behavior predictable.
Verify connectivity before running a full playbook against new infrastructure: . A hostname that changed since the inventory was written produces failures that look like network problems.
Fact caching is a subtler trap. Ansible gathers host facts at playbook start: IP addresses, OS version, disk layout. In pipelines where infrastructure changes mid-run, those facts go stale and produce bugs that are genuinely hard to trace. Disable fact caching or force a refresh with when current state matters.
Install ansible-core on any Linux or macOS machine using pip:
Verify with . The output shows the ansible-core version, the Python path, and the config file location. On Windows, install via WSL2 since the Ansible control node does not run natively on Windows.
If you're following along with the Jenkins demo below, start a GitHub Codespace from . ansible-core is pre-installed and you can skip local setup entirely.
This demo automates the setup of a Jenkins CI/CD environment on an EC2 instance: provisions the infrastructure, Ansible handles configuration, and Docker runs Jenkins as a container for a portable, isolated deployment.
Below is a diagram of what you will build:
  * : You'll use Terraform to automate the creation of your EC2 instance and related networking resources. We won't spend too much time explaining Terraform since our focus is on Ansible.
  * : Ansible will install Docker, configure the Jenkins environment, and run Jenkins inside a Docker container on the EC2 instance.
  * : You will use Docker to run Jenkins as a container on your EC2 instance.


The first step is to create the infrastructure needed for our Jenkins environment using Terraform.
: Start by navigating to the directory where your Terraform configuration files are located.
: Initialize your Terraform environment to download the necessary provider plugins and prepare your working directory.
: Apply the Terraform configuration to create your AWS infrastructure. The flag will bypass manual approval for the changes. Be careful using this flag in production environments.
  * Security groups to control access to your EC2 instance
  * An EC2 instance where Jenkins will be installed
  * An Elastic IP for public access to the instance


After the process is completed, Terraform will output critical information, such as the public IP address of the EC2 instance and a private SSH key for secure access.
### **Step 2: Prepare Ansible Inventory and SSH Key**
With the EC2 instance created, we need to prepare the Ansible inventory file, which Ansible uses to know which hosts to manage. 
Additionally, we’ll prepare the SSH key that Ansible will use to authenticate with the EC2 instance.
: Replace the placeholder in the Ansible inventory file with the actual public IP address of your EC2 instance. This can be done using a simple command.
After updating, verify the inventory file to confirm the IP address was inserted correctly.
: Extract the private key generated by Terraform and save it to a file that Ansible can use to connect to the EC2 instance.
Set the correct permissions on the private key file to secure it.
### **Step 3: Configure the EC2 instance with Ansible**
Now that the infrastructure is in place and the inventory and SSH key are prepared, you can move on to configuring the EC2 instance using Ansible.
: Change your directory to where the Ansible playbook is located.
: Execute the playbook to configure the EC2 instance. It installs Docker, sets up the Jenkins container, and verifies the service is running.
The playbook file consists of several tasks that automate the following steps, more details will be provided in a later section:
  1. : These are required for installing Python packages and handling compressed files.
  2. : Adds the GPG key for the official Docker repository.
  3. : Configures the Docker repository in your package manager.
  4. : Installs the latest version of Docker CE (Community Edition).
  5. : Installs the Docker module for Python, enabling Ansible to manage Docker containers.
  6. : Pulls a pre-built Jenkins Docker image from Docker Hub.
  7. : Sets the correct ownership and permissions for Jenkins data directories.
  8. : Creates and starts the Jenkins container, mapping necessary ports and volumes.


Once the Ansible playbook has completed its execution, Jenkins should be up and running on your EC2 instance. Let’s verify that everything is set up correctly.
: Open a web browser and navigate to the public IP address of your EC2 instance using port 8080.
This will bring up the Jenkins login page:
: The initial Jenkins admin password is stored on the EC2 instance. SSH into the instance to retrieve it as shown below, replacing ‘public_ip’ with your public IP.
Copy this password and use it to log into Jenkins.
: After logging in, follow the Jenkins setup wizard to install recommended plugins or skip the plugin installation to expedite the process. Once completed, your Jenkins instance will be ready to use.
## **Inventory File and the Ansible Playbook: A Deeper Dive**
  * To set up your Ansible environment, you need to create an inventory file that stores client details, such as hostnames or IP addresses and SSH ports.
  * You can use SSH keys to connect to clients and simplify the process.


Ansible uses the inventory file to manage remote machines and network devices. 
Here is the inventory file that you used in the demo with comments:
You can use Ansible ad hoc commands to issue some commands on one or several servers. They are useful for tasks you rarely repeat. Therefore, you will mostly resort to using Playbooks. 
To write your playbook, you need to define the desired state of a system using Ansible playbook commands. Below is the file with comments.
env zero connects directly to your Git repository, version-controls your Ansible runs, and gives your team a shared control plane without modifying a single YAML file. 
Every run is now in the system. In the env zero UI, create a project and define an environment using an Ansible template. Set the Ansible version, paste in the SSH key Terraform generated, and point the environment at your GitHub repository.
The SSH key used here corresponds to the private key generated earlier with Terraform, giving Ansible authenticated access to your EC2 instance.
Specify the folder containing the playbook, then set as an environment variable. That's the only configuration change needed beyond what Terraform already produced.
Trigger a run. env zero clones the repo, loads variables, and executes the playbook.
After approval, every task from the CLI demo above runs inside the platform. The deployment that lived in your terminal is now tracked, auditable, and repeatable by anyone on the team with the right access.
The result: every Ansible run is tracked with full audit logs, role-based access control (RBAC) governs who can trigger deployments, and drift detection runs continuously against live infrastructure. env zero works with every IaC framework, including Terraform, OpenTofu, Pulumi, and CloudFormation, so teams that mix tools across projects don't need separate control planes for each one. 
The covers how governance fits into the full IaC lifecycle, from the first playbook to enterprise-scale policy enforcement.
Running Ansible locally works for a single engineer. Once multiple people run playbooks against shared infrastructure, questions multiply: who ran what, when did it succeed, why did it fail last Tuesday? env zero adds a control plane over your existing playbooks, with role-based access, approval workflows, full audit logs, and drift detection, without changing a line of YAML.
Ready to write your first Ansible playbook? Our covers YAML syntax, handlers, variables, and a full step-by-step deployment example.
####  **Q: What is the difference between Ansible and Jenkins?** ‍
Ansible is an automation tool primarily for configuration management, whereas Jenkins is a CI/CD tool focused on automating software builds, tests, and deployments. They serve different purposes but can complement each other. Here’s a quick comparison:  
 |  
|  |  
#### **Q: How do I create a directory in Ansible?**
**To c
---
URL: https://www.whizlabs.com/blog/ansible-introduction/
Conteúdo Extraído:
Looking at the present state of affairs, automation is the new trend in every sector. Automation finds prominent applications across different sectors such as advertising, marketing, sales, cloud, social media, and database management. Addressing the trouble of repetitive tasks, automation is here to stay! In this brief ansible tutorial, we shall take a look at one of the popular IT automation engines, i.e. Ansible. 
The primary task of ansible is configuration management. make it an ideal alternative for obtaining the desired state in a particular infrastructure with the least human effort. In this article, we shall take a look at the ansible architecture, how it works, and various ansible advantages. Most important of all, the discussion would highlight the role of playbooks in Ansible. If you’re an Ansible professional preparing for an , this introduction is a good start for you. So, let’s learn more about ansible.
The first point of interest in this discussion should be on what is ansible. However, let us take a look at some facts about Ansible. According to the , the Ansible user base got increased by 50%. Ansible also has its top-level topic among GitHub searches that leads to more than 5000 databases of Ansible content. Ansible also made to the top 10 of all GitHub projects in different categories according to the . 
The ever-increasing community of Ansible and the new features such as Ansible meetups and community working groups indicate Ansible’s popularity. Considering these facts about Ansible, an Ansible tutorial can help you get a superficial idea about this configuration management tool. So, now we shall get to the definition of ansible, shall we?
When you find a question asking about what is ansible, the first thing on your mind should be ‘automation’! Ansible is an open-source IT automation engine ideal for application deployment, cloud provisioning, and intra-service orchestration. It is also helpful for automaton of many other IT tools. 
Ansible provides exceptional ease of deployment without the need for custom security infrastructure or any agents. It depends on playbooks for describing automation jobs which is easy to understand. We shall reflect on playbooks in Ansible later on in this brief Ansible tutorial. Another interesting fact about ansible is its design for multi-tier deployment. So, with Ansible, you do not have to manage one system at a time.
On the contrary, Ansible prepares the IT infrastructure with a description of interrelation between all the systems. We shall also reflect on how ansible works in this discussion. However, before that, let us find out more about reasons to use Ansible. And, we are not talking about just the advantages here.
The foremost agenda in this Ansible tutorial while discussing reasons to use ansible shall start with configuration management. If you have a background in development or operations or you are a DevOps professional, then you must have gone through a series of processes. It may have been logging into a server for changing configuration option, restarting a service or installing a package. 
Must have been quite easy logging in through SSH and making changes to the application before logging out, wasn’t it? However, imagine that you face the same issue after some weeks or months! By now, you must have forgotten about how you achieved the fix in the first place. Therefore, you can use Ansible for managing servers with higher speed, consistency, and iteration. 
The prominent highlight you can find in almost any Ansible tutorial is Ansible’s simplicity. Ansible is easy to understand as compared to other configuration management tools and also provides credible efficiency and functionality. You can also find other prominent reasons to use Ansible as we move ahead gradually in our discussion.
> Preparing for an Ansible interview? Go through these and get ready to crack the Ansible interview.
The next important element in almost every ansible tutorial refers to the architecture of ansible. An understanding of the different elements in the architecture of Ansible can also support our understanding of how ansible work. The six prominent components of Ansible include modules, module utilities, inventory, playbooks, plugins, APIs, and the Ansible search path. Let us discuss each of them briefly as a promising addition to this brief introductory guide on Ansible. 
The first element in ansible architecture refers to modules. Ansible works through connecting to different nodes and pushing out scripts known as “ansible modules” on them. The modules accept parameters describing the desired state of a system. Subsequently, ansible ensures execution of the modules followed by removing them upon finishing. The default method for executing modules is over SSH. 
The library of modules can exist on any machine without the need for servers, databases, or daemons. Ansible gives much-needed flexibility for scripting your modules. The text editor terminal program and the version control system in Ansible can help in tracking changes in content. Furthermore, you can write specialized modules in languages such as Ruby, bash, or Python, which return JSON. 
The next important addition to the architecture of Ansible is module utilities. Module utilities are one of the major reasons for simple ansible usage. In cases of multiple modules using the same code, Ansible ensures storage of the functions as module utilities. The module utilities help in reducing duplication and maintenance. The example of a code that parses URLsis an ideal reference for module utilities. The code can be “lib/ansible/module_utils/url.py.” Also, you have the flexibility to write your module utilities. Python or PowerShell is ideal for writing module utilities.
Plugins are also one of the common entries in the architecture of ansible found commonly in every ansible documentation. They are known for improving the core functionality of Ansible. Plugins execute on control node in the “/usr/bin/ansible” process rather than executing on a remote system like modules. They provide extensions and options for core functionalities in Ansible. 
The core functionalities include data transformation, connecting to inventory, logging output, and others. Although you can find a fair number of usable plugins at your disposal when you ship in Ansible, you could also write some plugins on your own. One instance can involve writing an inventory plugin for connecting to any data source returning JSON. Python is the sole language for writing ansible plugins.
The next important element in the architecture of ansible refers to Inventory. Ansible provides a representation of machines that it manages in a file which is responsible for putting all the managed machines. You can assign managed machines to groups of own choosing. Every ansible documentation would outline the role of inventory in ansible. 
You don’t need any additional SSL signing server for adding new machines. Therefore, there are no issues in deciding on reasons for which specific machines do not get linked for DNS issues or obscure NTP. Ansible could derive inventory, variable, and group information from different sources such as Rackspace, EC2, OpenStack, and others. The example of a plain text inventory is shown as follows.
After listing inventory hosts, you can assign variables to them in simple text files. You can assign variables directly in the inventory file or the subdirectory known as ‘group_vars/’ or ‘host_vars/.’
Ansible APIs are used as transport for Cloud services whether used public or private. As Ansible API documentation is under construction, there is no more information available about APIs.
> Certification helps the professionals to validate their skills and get global recognition for them. Check out the list of and be determined to get one!
Now, we shall shed some light on the backbone of ansible, i.e., playbooks. As we know until now, playbooks help in the description of automation jobs, and it uses the very simple YAML. YAML stands for Yet Another Markup Language, and its unique highlight is that it is in human-readable form. Any ansible-playbook tutorial would show that YAML is a data serialization language ideal for configuring files. Let us reflect further on Ansible playbooks to clarify our understanding of Ansible’s working.
Simply put, playbooks are the files in which you write Ansible code. Playbooks are core features in Ansible and provide information regarding the execution tasks to Ansible. Think of playbooks as a to-do list for Ansible! 
You can observe details on playbook structure in any ansible-playbook tutorial. The structure of playbook involves many plays. Each play has to serve the function of mapping a set of instructions defined concerning a specific host. Another important concern in playbooks refers to the strict-typed nature of YAML. Even if YAML is in human-readable format, you need to take extra care when writing YAML files. 
You can use a simple editor such as notepad++ as a YAML editor. All you have to do is open notepad++, copy and paste “(Language → YAML)” YAML for changing the language to YAML. Keep in mind that a YAML always starts with three hyphens (—). Now, let us take a look at an example of creating a playbook. The following example shows a sample YAML file.

```


















-name: Ensure the installed service is enabled and running




```

The sample playbook shows the basic syntax for a playbook. You have to save the sample playbook with the filename ‘test.yml.’ A YAML syntax should always follow the appropriate indentation, and you should be additionally careful in writing the syntax. Now, let us describe the important components noted in the above sample playbook. The following elements in this ansible tutorial are also known as YAML tags. The different YAML tags in the example mentioned above are ‘name,’ ‘hosts,’ ‘vars,’ and ‘tasks.’ A description of the tags can help in improving your knowledge of ansible usage.
The ‘name’ YAML tag provides a specification for the name of the Ansible playbook. The ‘name’ YAML tag describes the work of the playbook. 
The ‘hosts’ YAML tag is also an important requirement playbook description in every ansible tutorial. The ‘hosts’ tag provides the specification of the lists of hosts or host group which you have to run a task. This is a mandatory field in the playbook as it informs Ansible about the hosts on which it should run listed tasks. You can run tasks on the same machine or a remote machine. You can also run tasks on multiple machines, thereby implying the possibility of a group of hosts entry. 
The ‘vars’ YAML tag in ansible is also an important concern in almost any Ansible tutorial. This YAML tag helps in the definition of the variable for use in a playbook. The use of ‘vars’ in Ansible resembles variables in the case of any programming language. 
The final element in an Ansible playbook refers to ‘tasks’ YAML tag. This YAML tag is a list of actions that Ansible should perform. The major use of ‘tasks’ YAML tag is in debugging the playbook.
On a concluding note to this Ansible tutorial, let us reflect on the future that Ansible holds for IT automation. For one mention, Ansible is a definite improvement over other configuration management systems. We can note that Ansible is agentless as you can install ansible only on the control machine. SSH can take care of connecting remote machines for you. 
The thorough and simple documentation of Ansible is a formidable mention among ansible advantages. This can promote Ansible adoption, won’t it? An open-source instrument with a human-readable language, i.e., YAML can also appeal to many users in the automation landscape. So, if you have developed an interest in ansible recently, then you have a long way to go! This discussion can serve as a helpful guide for your ansible journey.
In , the task of development and operations is integrated, which is very important for designing test-driven applications. Ansible provides a stable environment for development and operation for integration and thus, results in smooth orchestration. So, if you are a DevOps professional, start learning Ansible now! You can also check out our if you are preparing for any DevOps certification like; .
Dharmalingam.N holds a master degree in Business Administration and writes on a wide range of topics ranging from technology to business analysis. He has a background in Relationship Management. Some of the topics he has written about and that have been published include; project management, business analysis and customer engagement.
  * Top 10 Highest Paying Cloud Certifications in 2024
  * 12 AWS Certifications – Which One Should I Choose?
  * 11 Kubernetes Security Best Practices you should follow in 2024
  * How to run Kubernetes on AWS – A detailed Guide!
  * Free questions on CompTIA Network+ (N10-008) Certification Exam
  * 30 Free Questions on Microsoft Azure AI Fundamentals (AI-900)
  *   * How to Create CI/CD Pipeline Inside Jenkins ?



---
URL: https://www.devopsschool.com/blog/the-complete-ansible-tutorial-concepts-architecture-playbooks-and-real-world-examples/
Conteúdo Extraído:
Explore trusted cosmetic hospitals and make a confident choice for your transformation. 
“Invest in yourself — your confidence is always worth it.” 
Start your journey today — compare options in one place. 
Here is a based on your notes, structured as a long-form guide. Every topic, term, and example is included, with deep explanations and practical demonstrations.
is an open-source configuration management, application deployment, and server orchestration tool created by Red Hat. It enables IT professionals and developers to , ensuring consistent and repeatable outcomes.
  * Automates the setup, maintenance, and configuration of servers.
  * Efficiently manages large groups of servers from a single control point.
  * Ansible is built using Python, making it cross-platform and highly extensible.


  * Paid UI-based solution for enterprise teams (now called Red Hat Ansible Automation Platform).
  * Free, open-source UI for Ansible (community-supported version of Tower).


  * Deploy and configure system software, antivirus, company policies, etc.
  * Automate the deployment of application code and related services.
  * If you need to change files, directories, users, packages, or services across many servers, Ansible is ideal.


  * Apply changes to hundreds or thousands of servers at once, reducing manual effort.
  * Achieve consistent, predictable changes on every server.


  
operation—no special software required on managed hosts.
  * (the machine from which you run Ansible).


```
Human (You)
   |
   V
Ansible Control Server (ACS)
   |
   V
Ansible Remote Server(s) (ARS)

```
  
No Ansible agent is installed on remote servers; communication is via (Linux/Unix) or (Windows).


A is a reusable, standalone script (written in Python) that performs a specific task. They reside on the ACS and run on ARS.


A is a piece of code that adds extra functionality to Ansible itself (runs on ACS). Types include connection plugins, callback plugins, lookup plugins, etc.
The is a file or script that lists the IPs/hostnames of the ARS to be managed.
You can provide the inventory as a file, inline on the command line, or generate it dynamically.
A is a YAML file that defines a set of tasks to execute on remote hosts using Ansible modules.

```
---
- name: Update web servers
  : web
  :
    - name: Install Apache  ubuntu
      ansible.builtin.apt:
        name: 
        : latest
    - name: Copy index.html
      ansible.builtin.copy:
        src: index.html
        : www/html/index.html
    - name: Starting Apache Server
      ansible.builtin.service:
        name: 
        : started

```

  1. e.g., “Set up a web server”.
  2. What should happen? (install apache2, copy files, start service).
  3. Find the relevant module and parameters.


```
---
- name: Setup Webserver
  : web
  :
    - name: Install Apache2
      ansible.builtin.apt:
        name: apache2
        : latest
    - name: Copy app file
      ansible.builtin.copy:
        src: app.html
        : www/html/app.html
    - name: Start apache2
      ansible.builtin.service:
        name: apache2
        : started

```

let you run one-off tasks without writing a playbook.

```

ansible localhost -m apt -a 


ansible localhost -m service -a 


ansible localhost -m service -a 

```

```

ansible localhost -m user -a 


ansible localhost -m group -a 


ansible localhost -m copy -a 


ansible localhost -m fetch -a 


ansible localhost -m shell -a 


ansible localhost -m file -a 


ansible localhost -m apt -a 


ansible localhost -m reboot


ansible localhost -m command -a 


ansible localhost -m shell -a 

```

```
ansible all -i ,, -m apt -a 
ansible all -i ,, -m service -a  -u ubuntu -b --key-file=node.pem

```

```
ansible all -i inventory -m apt -a  -u ubuntu -b --key-file=node.pem
ansible all -i inventory -m service -a  -u ubuntu -b --key-file=node.pem

```

```
ansible-playbook -i inventory web.yaml -u ubuntu -b --key-file=node.pem
ansible-playbook -i inventory db.yaml -u ubuntu -b --key-file=node.pem
ansible-playbook -i inventory master.yaml -u ubuntu -b --key-file=node.pem

```

You can include other playbooks or tasks within your main playbook:

```
- hosts: web
  tasks:
    - debug: msg=
    - name:  task  in play
      : web.yaml
    - name:  task  in play
      : db.yaml

- hosts: db
  tasks:
    - debug: msg=
    - name:  task  in play
      : web.yaml
    - name:  task  in play
      : db.yaml

```

Variables allow you to parametrize your playbooks for flexibility and reuse.


```
---
- name: Update web servers
  hosts: web
  vars:
    myname: 
    age: 
    packagename: 
    servicename: 
  vars_files:
    - 
  vars_prompt:
    - name: 
      prompt: 
      : no

  tasks:
    - name: Install Apache in ubuntu
      ansible.builtin.apt:
        name: 
        state: latest
    - name: Copy index.html
      ansible.builtin.copy:
        src: index.html
        dest: //www/html/index.html
    - name: Starting a Apache Server
      ansible.builtin.service:
        name: 
        state: started
    - name:  name  age
      ansible.builtin.debug:
        msg: "My Name is {{ myname }} and My age is {{ age }}"
    - name:  version from prompt
      ansible.builtin.debug:
        : version
    - name: Register   file 
      shell: 
      args:
        chdir: 
      register: find_output
    - debug:
        : find_output
    - debug:
        : find_output.stdout_lines
    - debug:
        : find_output.stdout_lines[]

```

```
ansible-playbook -i inventory vars.yaml -u ubuntu -b --key-file=node.pem

```

Roles provide a and make code reusable and shareable.

```
roles/
  web/
    tasks/
      main.yaml
    handlers/
      main.yaml
    files/
    templates/
    vars/
      main.yaml
    defaults/
      main.yaml

```

```
---
- name: Update web servers
  hosts: web
  roles:
    - web

```

```
ansible-playbook -i inventory site.yaml -u ubuntu -b --key-file=node.pem

```

  * Special tasks triggered by “notify” for things like restarts.
  * Static files to be copied to the remote host.


  * Safe to run multiple times (won’t break things)

  
**If you need more detailed sections, live scenarios, or want to expand on topics like dynamic inventories, Ansible Galaxy, or advanced Jinja2 templating, just let me know!**
I’m a DevOps/SRE/DevSecOps/Cloud Expert passionate about sharing knowledge and experiences. I have worked at . I share tech blog at , travel stories at , stock market tips at , health and fitness guidance at , product reviews at , and SEO strategies at 
Compare heart hospitals by city and services — all in one place. 
_Excellent and well-structured tutorial! The way the article explains Ansible concepts, architecture, playbooks, and real-world examples makes it much easier for beginners and DevOps learners to understand automation. A very useful resource for anyone getting started with Ansible._
DevOpsSchool has introduced a series of professional certification courses designed to enhance your skills and expertise in cutting-edge technologies and methodologies. Whether you are aiming to excel in development, security, or operations, these certifications provide a comprehensive learning experience. Explore the following programs: 
  * - Learn the fundamentals and advanced concepts of DevOps practices and tools. 
  * - Master the integration of security within the DevOps workflow. 
  * - Gain expertise in Site Reliability Engineering and ensure reliability at scale. 
  * - Dive into Machine Learning Operations and streamline ML workflows. 
  * - Discover AI-driven operations management for next-gen IT environments. 


Explore our , , and programs at . Gain the expertise needed to excel in your career with hands-on training and globally recognized certifications. 

---
URL: https://docs.ansible.com/projects/ansible/latest/tips_tricks/sample_setup.html
Conteúdo Extraído:


Join us at to learn about Ansible Automation Platform | May 11-14, 2026
This is the (stable) Ansible community documentation. For Red Hat Ansible Automation Platform subscriptions, see for version details.
The ansible-core 2.19/Ansible 12 release has made **significant templating changes that might require you to update playbooks and roles**. The templating changes enable reporting of numerous problematic behaviors that went undetected in previous releases, with wide-ranging positive effects on security, performance, and user experience. You should validate your content to ensure compatibility with these templating changes before upgrading to ansible-core 2.19 or Ansible 12. See the to understand where you may need to update your playbooks and roles.
You have learned about playbooks, inventory, roles, and variables. This section combines all those elements and outlines a sample setup for automating a web service.
The sample setup organizes playbooks, roles, inventory, and files with variables by function. Tags at the play and task level provide greater granularity and control. This is a powerful and flexible approach, but there are other ways to organize Ansible content. Your usage of Ansible should fit your needs, so feel free to modify this approach and organize your content accordingly.
This layout organizes most tasks in roles, with a single inventory file for each environment and a few playbooks in the top-level directory:

```
production                # inventory file for production servers
staging                   # inventory file for staging environment


   group1.yml             # here we assign variables to particular groups


   hostname1.yml          # here we assign variables to particular systems


library/                  # if any custom modules, put them here (optional)
module_utils/             # if any custom module_utils to support modules, put them here (optional)
filter_plugins/           # if any custom filter plugins, put them here (optional)

site.yml                  # main playbook
webservers.yml            # playbook for webserver tier
dbservers.yml             # playbook for dbserver tier
tasks/                    # task files included from playbooks
    webservers-extra.yml  # <-- avoids confusing playbook with task files

```


```
roles/
    common/               # this hierarchy represents a "role"
        tasks/            #
            main.yml      #  <-- tasks file can include smaller files if warranted
        handlers/         #
            main.yml      #  <-- handlers file
        templates/        #  <-- files for use with the template resource
            ntp.conf.j2   #  <------- templates end in .j2
        files/            #
            bar.txt       #  <-- files for use with the copy resource
            foo.sh        #  <-- script files for use with the script resource
        vars/             #
            main.yml      #  <-- variables associated with this role
        defaults/         #
            main.yml      #  <-- default lower priority variables for this role
        meta/             #
            main.yml      #  <-- role dependencies and optional Galaxy info
        library/          # roles can also include custom modules
        module_utils/     # roles can also include custom module_utils
        lookup_plugins/   # or other types of plugins, like lookup in this case

    webtier/              # same kind of structure as "common" was above, done for the webtier role
    monitoring/           # ""
    fooapp/               # ""

```

By default, Ansible assumes your playbooks are stored in one directory with roles stored in a sub-directory called . With more tasks to automate, you can consider moving your playbooks into a sub-directory called . If you do this, you must configure the path to your directory using the setting in the file.
You can also put each inventory file with its / in a separate directory. This is particularly useful if your / do not have that much in common in different environments. The layout could look like this example:
> 
```


      hosts               # inventory file for production servers

         group1.yml       # here we assign variables to particular groups


         hostname1.yml    # here we assign variables to particular systems



      hosts               # inventory file for staging environment

         group1.yml       # here we assign variables to particular groups


         stagehost1.yml   # here we assign variables to particular systems
















```

This layout gives you more flexibility for larger environments, as well as a total separation of inventory variables between different environments. However, this approach is harder to maintain, because there are more files. For more information on organizing group and host variables, see .
These sample group and host files with variables contain the values that apply to each machine or a group of machines. For example, the data center in Atlanta has its own NTP servers. As a result, when setting up the file, you could use similar code as in this example:
Similarly, hosts in the webservers group have some configuration that does not apply to the database servers:
Default values, or values that are universally true, belong in a file called :
If necessary, you can define specific hardware variance in systems in the directory:
If you use , Ansible creates many dynamic groups automatically. As a result, a tag like will load in variables from the file automatically.
You can access host variables with a special variable called . See for a list of these variables. The variable can access only host-specific variables, not group variables.
With this setup, a single playbook can define the entire infrastructure. The playbook imports two other playbooks. One for the webservers and one for the database servers:
The playbook, also at the top level, maps the configuration of the webservers group to the roles related to the webservers group:
With this setup, you can configure your entire infrastructure by running . Alternatively, to configure just a portion of your infrastructure, run . This is similar to the Ansible parameter but a little more explicit:
##  Sample task and handler files in a function-based role
Ansible loads any file called in a role sub-directory. This sample file configures NTP:
> 
```
























```

Here is an example handlers file. Handlers are only triggered when certain tasks report changes. Handlers run at the end of each play:
The basic organizational structure described above enables a lot of different automation options. To reconfigure your entire infrastructure:
To reconfigure only the first 10 webservers in Boston, and then the next 10:
The sample setup also supports basic ad hoc commands:
To discover what tasks would run or what hostnames would be affected by a particular Ansible command:
> 
```
# confirm what task names would be run if I ran this command and said "just ntp tasks"
ansible-playbook-iproductionwebservers.yml--tagsntp--list-tasks

# confirm what hostnames might be communicated with if I said "limit to boston"
ansible-playbook-iproductionwebservers.yml--limitboston--list-hosts

```

The sample setup illustrates a typical configuration topology. When you do multi-tier deployments, you will likely need some additional playbooks that hop between tiers to roll out an application. In this case, you can augment with playbooks like . However, the general concepts still apply. With Ansible you can deploy and configure using the same utility. Therefore, you will probably reuse groups and keep the OS configuration in separate playbooks or roles from the application deployment.
Consider “playbooks” as a sports metaphor – you can have one set of plays to use against all your infrastructure. Then you have situational plays that you use at different times and for different purposes.
If a playbook has a directory relative to its YAML file, you can use this directory to add Ansible modules automatically to the module path. This organizes modules with playbooks. For example, see the directory structure at the start of this section.     
Learn how to extend Ansible by writing your own modules     
Got questions? Need help? Want to share your ideas? Visit the Ansible communication guide

---
URL: https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_plugins.html [TRUNCADO]
Conteúdo Extraído:
Join us at to learn about Ansible Automation Platform | May 11-14, 2026
This is the (stable) Ansible community documentation. For Red Hat Ansible Automation Platform subscriptions, see for version details.
The ansible-core 2.19/Ansible 12 release has made **significant templating changes that might require you to update playbooks and roles**. The templating changes enable reporting of numerous problematic behaviors that went undetected in previous releases, with wide-ranging positive effects on security, performance, and user experience. You should validate your content to ensure compatibility with these templating changes before upgrading to ansible-core 2.19 or Ansible 12. See the to understand where you may need to update your playbooks and roles.
Plugins augment Ansible’s core functionality with logic and features that are accessible to all modules. Ansible collections include a number of handy plugins, and you can easily write your own. All plugins must:


Once you’ve reviewed these general guidelines, you can skip to the particular type of plugin you want to develop.
You must write your plugin in Python so it can be loaded by the and returned as a Python object that any module can use. Since your plugin will execute on the control node, you must write it in a .
You should return errors encountered during plugin execution by raising or a similar class with a message describing the error. When wrapping other exceptions into error messages, you should always use the Ansible function to ensure proper string compatibility across Python versions:
Since Ansible evaluates variables only when they are needed, filter and test plugins should propagate the exceptions and to ensure undefined variables are only fatal when necessary.
Check the different and see which one applies best to your situation. Check the section on the specific plugin type you’re developing for type-specific error handling details.
You must convert any strings returned by your plugin into Python’s unicode type. Converting to unicode ensures that these strings can run through Jinja2. To convert strings:
To define configurable options for your plugin, describe them in the section of the python file. Callback and connection plugins have declared configuration requirements this way since Ansible version 2.4; most plugin types now do the same. This approach ensures that the documentation of your plugin’s options will always be correct and up-to-date. To add a configurable option to your plugin, define it in this format:

```

















```
    
List of environment variables that can be used to set this option. Each entry includes a field specifying the environment variable name. The name should be in uppercase and should be prefixed with the collection name. Multiple environment variables can be listed for the same option. The last set environment variable in the list takes precedence if multiple are set. This is commonly used for plugins (especially inventory plugins) to allow configuration through environment variables. Examples: ,      
List of configuration file settings that can be used to set this option. Each entry includes a field for the configuration file section and a field for the configuration key. Both should be in lowercase and should be prefixed with the collection name. Multiple configuration settings can be listed for the same option. The last set configuration setting in the list takes precedence if multiple are set. This allows plugins to be configured with ansible.cfg. Example:      
List of Ansible variables that can be used to set this option. Each entry includes a field specifying the variable name. The name should be in lowercase and should be prefixed with the collection name. Multiple variables can be listed for the same option. The last set variable in the list takes precedence if multiple are set. Variables follow Ansible’s variable precedence rules. This allows plugins to be configured with Ansible variables. Example: 
> The precedence rules for configuration sources are listed below, starting with the highest precedence values:


To access the configuration settings in your plugin, use . Some plugin types handle this differently:
  * Become, callback, connection and shell plugins are guaranteed to have the engine call .
  * Lookup plugins always require you to handle it in the method.
  * Inventory plugins are done automatically if you use the method. If not, you must use .
  * Cliconf, httpapi and netconf plugins indirectly piggy back on connection plugins.
  * Vars plugin settings are populated when first accessed (using the or method.


If you need to populate settings explicitly, use a call.
Configuration sources follow the precedence rules for values in Ansible. When there are multiple values from the same category, the value defined last takes precedence. For example, in the above configuration block, if both and are defined, the value of the option will be the value of . Refer to for further information.
Plugins that support embedded documentation (see for the list) should include well-formed doc strings. If you inherit from a plugin, you must document the options it takes, either through a documentation fragment or as a copy. See for more information on correct documentation. Thorough documentation is a good idea even if you’re developing a plugin for local use. 

In ansible-core 2.14 we added support for documenting filter and test plugins. You have two options for providing documentation:
    
  * Define a Python file that includes inline documentation for each plugin.
  * Define a Python file for multiple plugins and create adjacent documentation files in YAML format.


Action plugins let you integrate local processing and local data with module functionality.
To create an action plugin, create a new class with the Base(ActionBase) class as the parent:
From there, execute the module using the method to call the original module. After successful execution of the module, you can modify the module return data.
For example, if you wanted to check the time difference between your Ansible control node and your target machine(s), you could write an action plugin to check the local time and compare it to the return data from Ansible’s module:

```

# Make coding more python3-ish, this is required for contributions to Ansible
   
  

 
 



      
          
          
          
                                             
                                              
          
          
          
                
                   
                      

         
               
                
              
              
              

         

```

This code checks the time on the control node, captures the date and time for the remote machine using the module, and calculates the difference between the captured time and the local time, returning the time delta in days, seconds and microseconds.
For practical examples of action plugins, see the source code for the 
Cache plugins store gathered facts and data retrieved by inventory plugins.
Import cache plugins using the cache_loader so you can use and . If you import a cache plugin directly in the code base, you can only access options by the , and you break the cache plugin’s ability to be used by an inventory plugin.
There are two base classes for cache plugins, for database-backed caches, and for file-backed caches.
To create a cache plugin, start by creating a new class with the appropriate base class. If you’re creating a plugin using an method you should initialize the base class with any provided args and kwargs to be compatible with inventory plugin cache options. The base class calls . After the base class method is called should be used to access cache options.
New cache plugins should take the options , , and to be consistent with existing cache plugins.
If you use the , you must implement the methods , , , , , , and . The method should return a boolean that indicates if the key exists and has not expired. Unlike file-based caches, the method does not raise a KeyError if the cache has expired.
If you use the , you must implement and methods that will be called from the base class methods and .
If your cache plugin stores JSON, use in the or method and in the or method.
For example cache plugins, see the source code for the .
Note that cache plugin implementation is an internal detail, and should not be relied upon by external uses such as interrogation or consumption in a playbook.
It is assumed that a cache produced at any point in time, is usable at any future point in time, as the underlying implementation, or information provided within may change.
If the planned use case of a cache is external interrogation or consumption, we recommend to be explicit about the fetching and storing of that data, such as creating a playbook that gathers facts and stores them in the format you need them in, and then stores that data explicitly outside of the concept of a cache, where it can be relied upon.
Callback plugins add new behaviors to Ansible when responding to events. By default, callback plugins control most of the output you see when running the command line programs.
To create a callback plugin, create a new class with the Base(Callbacks) class as the parent:
From there, override the specific methods from the CallbackBase that you want to provide a callback for. For plugins intended for use with Ansible version 2.0 and later, you should only override methods that start with . For a complete list of methods that you can override, please see in the directory.
The following is a modified example of how Ansible’s timer plugin is implemented, but with an extra option so you can see how configuration works in Ansible version 2.4 and later:

```
# Make coding more python3-ish, this is required for contributions to Ansible
   
  

# not only visible to ansible-doc, it also 'declares' the options the plugin requires and how to configure them.
  





version_added: "2.0"  # for collections, use the collection version, not the Ansible version

    - This callback just adds total play duration to the play stats.


    description: format of the string shown to user at play end







 

 




    This callback module tells you how long your plays ran for.

      
      
      

    # only needed if you ship it and don't want to enable by default
      

    

      # make sure the expected objects are present, calling the base's __init__
       

      # start the timer when the plugin is loaded, the first play should start a few milliseconds after.
        

     
''' internal helper method for this callback '''
            
            
            

    # this is only event we care about for display, when the play shows its summary stats; the rest are ignored by the base class
     
        
          

      # Shows the usage of a config option declared in the DOCUMENTATION variable. Ansible will have set it when it loads the plugin.
      # Also note the use of the display object to print to screen. This is available to all callbacks, and you should use this over printing yourself
        

```

Note that the and definitions are required for properly functioning plugins for Ansible version 2.0 and later. is mostly needed to distinguish ‘stdout’ plugins from the rest, since you can only load one plugin that writes to stdout.
For example callback plugins, see the source code for the 
New in ansible-core 2.11, callback plugins are notified (by the ) of tasks. By default, only explicit tasks that users list in their plays are sent to callbacks.
There are also some tasks which are generated internally and implicitly at various points in execution. Callback plugins can opt-in to receiving these implicit tasks as well, by setting . Any object received by a callback hook will have an attribute, which can be consulted to determine whether the originated from within Ansible, or explicitly by the user.
Connection plugins allow Ansible to connect to target hosts so it can execute tasks on them. Ansible ships with many connection plugins, but only one can be used per host at a time. The most commonly used connection plugins are native , , and . All of these can be used with ad-hoc tasks and in playbooks.
To create a new connection plugin (for example, to support SNMP, Message bus, or other transports), copy the format of one of the existing connection plugins and drop it into directory on your .
Connection plugins can support common options (such as the flag) by defining an entry in the documentation for the attribute name (in this case ). If the common option has a non-null default, the plugin should define the same default since a different default would be ignored.
For example connection plugins, see the source code for the .
Filter plugins manipulate data. They are a feature of Jinja2 and are also available in Jinja2 templates used by the module. As with all plugins, they can be easily extended, but instead of having a file for each one you can have several per file. Most of the filter plugins shipped with Ansible reside in a .
Filter plugins do not use the standard configuration system described above, but since ansible-core 2.14 can use it as plain documentation.
Since Ansible evaluates variables only when they are needed, filter plugins should propagate the exceptions and to ensure undefined variables are only fatal when necessary.

```

    
   
       
   
       

```

For example filter plugins, see the source code for the .
Inventory plugins parse inventory sources and form an in-memory representation of the inventory. Inventory plugins were added in Ansible version 2.4.
You can see the details for inventory plugins in the page.
Lookup plugins pull in data from external data stores. Lookup plugins can be used within playbooks both for looping — playbook language constructs like and are implemented through lookup plugins — and to return values into a variable or parameter.
Lookup plugins are expected to return lists, even if just a single element.
Ansible includes many which can be used to manipulate the data returned by a lookup plugin. Sometimes it makes sense to do the filtering inside the lookup plugin, other times it is better to return results that can be filtered in the playbook. Keep in mind how the data will be referenced when determining the appropriate level of filtering to be done inside the lookup plugin.
Here’s a simple lookup plugin implementation — this lookup returns the contents of a text file as a variable:

```
# python 3 headers, required if submitting to Ansible
   
  

  


  version_added: "0.9"  # for collections, use the collection version, not the Ansible version


      - This lookup returns the contents from a file on the Ansible control node's file system.






            - Sample option that could modify plugin behavior.
            - This one can be set directly ``option1='x'`` or in ansible.cfg, but can also use vars or environment.





    - if read in variable context, the file can be interpreted as YAML if the content is valid to the parser.
    - this lookup does not understand globbing --- use the fileglob lookup instead.

  
 
 

  



       

      
      # this will already take into account env vars and ini config
       

      # lookups in general are expected to both take a list as input and output a list
      # this is done so they work with the looping construct 'with_'.
        
         
            

          # Find the file in the expected search path, using a class method
          # that implements the 'expected' search path for Ansible plugins.
              

          # Don't use print or your own logging, the display class
          # takes care of it in a unified way.
            
          
               
                     
                  
              
                  # Always use ansible error classes to throw 'final' exceptions,
                  #
---
URL: https://www.digitalocean.com/community/tutorials/configuration-management-101-writing-ansible-playbooks [TRUNCADO]
Conteúdo Extraído:
In a nutshell, server configuration management (also popularly referred to as IT Automation) is a solution for turning your infrastructure administration into a codebase, describing all processes necessary for deploying a server in a set of provisioning scripts that can be versioned and easily reused. It can greatly improve the integrity of any server infrastructure over time.
In a , we talked about the main benefits of implementing a configuration management strategy for your server infrastructure, how configuration management tools work, and what these tools typically have in common.
This part of the series will walk you through the process of automating server provisioning using Ansible, a configuration management tool that provides a complete automation framework and orchestration capabilities, while maintaining a goal of ultimate simplicity and minimalism. We will focus on the language terminology, syntax, and features necessary for creating a simplified example to fully automate the deployment of an Ubuntu 18.04 web server using Apache.
The following list contains all steps we need to automate in order to reach our goal:
  1. Apply a template to set up our custom virtual host


We’ll start by having a look at the terminology used by Ansible, followed by an overview of the main language features that can be used to write playbooks. At the end of the guide, you’ll find the contents of a full provisioning example to automate the steps described for setting up Apache on Ubuntu 18.04.
: this guide is intended to get you introduced to the Ansible language and how to write playbooks to automate your server provisioning. For a more introductory view of Ansible, including the steps necessary for installing and getting started with this tool, as well as how to run Ansible commands and playbooks, check our How to Install and Configure Ansible on Ubuntu 18.04 guide.
Before we can move to a more hands-on view of Ansible, it is important that we get acquainted with important terminology and concepts introduced by this tool.
The following list contains a quick overview of the most relevant terms used by Ansible:
  * : the machine where Ansible is installed, responsible for running the provisioning on the servers you are managing.
  * : an file that contains information about the servers you are managing.
  * : a file containing a series of procedures that should be automated.
  * : a block that defines a single procedure to be executed, e.g.: install a package.
  * : a module typically abstracts a system task, like dealing with packages or creating and changing files. Ansible has a multitude of built-in modules, but you can also create custom ones.
  * : a set of related playbooks, templates and other files, organized in a pre-defined way to facilitate reuse and share.
  * : a provisioning executed from start to finish is called a .
  * : global variables containing information about the system, like network interfaces or operating system.
  * : used to trigger service status changes, like restarting or reloading a service.


A task defines a single automated step that should be executed by Ansible. It typically involves the usage of a module or the execution of a raw command. This is how a task looks:

```
- name: This is a task
  apt: name=vim state=latest

```

The part is actually optional, but recommended, as it shows up in the output of the provisioning when the task is executed. The part is a built-in Ansible module that abstracts the management of packages on Debian-based distributions. This example task tells Ansible that the package should have its state changed to , which will cause the package manager to install this package in case it is not installed yet.
Playbooks are files containing a series of directives to automate the provisioning of a server. The following example is a simple playbook that perform two tasks: updates the cache and installs afterwards:

```
---
- hosts: all
  become: true
  tasks:
     - name: Update apt-cache 
       apt: update_cache=yes

     - name: Install Vim
       apt: name=vim state=latest

```

relies on indentation to serialize data structures. For that reason, when writing playbooks and especially when copying examples, you need to be extra careful to maintain the correct indentation.
Before the end of this guide we will see a more real-life example of a playbook, explained in detail. The next section will give you an overview of the most important elements and features that can be used to write Ansible playbooks.
Now that you are familiar with basic terminology and the overal format of playbooks and tasks in Ansible, we’ll learn about some playbook features that can help us creating more versatile automations.
There are different ways in which you can define variables in Ansible. The simplest way is by using the section of a playbook. The example below defines a variable that later is used inside a task:

```
---
- hosts: all
  become: true
  vars:
     package: vim
  tasks:
     - name: Install Package
       apt: name={{ package }} state=latest

```

The variable has a global scope, which means it can be accessed from any point of the provisioning, even from included files and templates.
Loops are typically used to repeat a task using different input values. For instance, instead of creating 10 tasks for installing 10 different packages, you can create a single task and use a loop to repeat the task with all the different packages you want to install.
To create a loop within a task, include the option with an array of values. The content can be accessed through the loop variable , as shown in the example below:

```
- name: Install Packages
  apt: name={{ item }} state=latest
  with_items:
     - vim
     - git
     - curl  

```

You can also use an to define your items:

```
---
- hosts: all
  become: true
  vars:
     packages: [ 'vim', 'git', 'curl' ]
  tasks:
     - name: Install Package
       apt: name={{ item }} state=latest
       with_items: "{{ packages }}"

```

Conditionals can be used to dynamically decide whether or not a task should be executed, based on a variable or an output from a command, for instance.
The following example will only shutdown Debian based systems:
The conditional receives as argument an expression to be evaluated. The task only gets executed in case the expression is evaluated to . In our example, we tested a to check if the operating system is from the Debian family.
A common use case for conditionals in IT automation is when the execution of a task depends on the output of a command. With Ansible, the way we implement this is by registering a variable to hold the results of a command execution, and then testing this variable in a subsequent task. We can test for the command’s exit status (if failed or successful). We can also check for specific contents inside the output, although this might require the usage of regex expressions and string parsing commands.
The next example shows two conditional tasks based on the output from a command. We will test for the exit status of the command, since we know it will fail to execute in case PHP is not installed on this server. The portion of the task is important to make sure the provisioning continues even when the command fails execution.

```
  Check if PHP is installed
   php_installed
   php v
   

  This task is only executed if PHP is installed
   var=php_install
   php_installedsuccess
  
  This task is only executed if PHP is NOT installed
   msg='PHP is NOT installed'
   php_installedfailed

```

The module used here is a useful module for showing contents of variables or debug messages. It can either print a string (when using the argument) or print the contents of a variable (when using the argument).
Templates are typically used to set up configuration files, allowing for the use of variables and other features intended to make these files more versatile and reusable. Ansible uses the template engine.
The following example is a template for setting up an Apache virtual host, using a variable for setting up the document root for this host:

```
<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    DocumentRoot {{ doc_root }}

    <Directory {{ doc_root }}>
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>

```

The built-in module is used to apply the template from a task. If you named the template file above , and you placed it in the same directory as your playbook, this is how you would apply the template to replace the default Apache virtual host:
Handlers are used to trigger a state change in a service, such as a or a . Even though they might look fairly similar to regular tasks, handlers are only executed when previously triggered from a directive in a task. They are typically defined as an array in a section of the playbook, but they can also live in separate files.
Let’s take into consideration our previous template usage example, where we set up an Apache virtual host. If you want to make sure Apache is restarted after a virtual host change, you first need to create a handler for the Apache service. This is how handlers are defined inside a playbook:
The directive here is important because it will be the unique identifier of this handler. To trigger this handler from a task, you should use the option:
We’ve seen some of the most important features you can use to begin writing Ansible playbooks. In the next section, we’ll dive into a more real-life example of a playbook that will automate the installation and configuration of Apache on Ubuntu.
Now let’s have a look at a playbook that will automate the installation of an Apache web server within an Ubuntu 18.04 system, as discussed in this guide’s introduction.
The complete example, including the template file for setting up Apache and an HTML file to be served by the web server, can be found . The folder also contains a Vagrantfile that lets you test the playbook in a simplified setup, using a virtual machine managed by .
The full contents of the playbook are available here for your convenience:

```



















  1.       copy: src=index.html dest={{ doc_root }}/index.html owner=www-data group=www-data mode=0644




  2.     - name: Set up Apache virtual host file











```

Let’s examine each portion of this playbook in more detail:
The playbook starts by stating that it should be applied to hosts in your inventory (). It is possible to restrict the playbook’s execution to a specific host, or a group of hosts. This option can be overwritten at execution time.
The portion tells Ansible to use privilege escalation (sudo) for executing all the tasks in this playbook. This option can be overwritten on a task-by-task basis.
Defines a variable, , which is later used in a task. This section could contain multiple variables.
The section where the actual tasks are defined. The first task updates the cache, and the second task installs the package .
The third task uses the built-in module to create a directory to serve as our document root. This module can be used to manage files and directories.
The fourth task uses the module to copy a local file to the remote server. We’re copying a simple HTML file to be served as our website hosted by Apache.
Finally, we have the section, where the services are declared. We define the handler that is notified from the fourth task, where the Apache template is applied.
Once you get the contents of this playbook downloaded to your Ansible control node, you can use to execute it on one or more nodes from your inventory. The following command will execute the playbook on hosts from your default inventory file, using SSH keypair authentication to connect as the current system user:
You can also use to limit execution to a single host or a group of hosts from your inventory:
If you need to specify a different SSH user to connect to the remote server, you can include the argument to that command:
For more information on how to run Ansible commands and playbooks, please refer to our guide on How to Install and Configure Ansible on Ubuntu 18.04.
Ansible is a minimalist IT automation tool that has a low learning curve, using for its provisioning scripts. It has a great number of built-in modules that can be used to abstract tasks such as installing packages and working with templates. Its simplified infrastructure requirements and simple language can be a good fit for those who are getting started with configuration management. It might, however, lack some advanced features that you can find with more complex tools like Puppet and Chef.
In the , we will see a practical overview of Puppet, a popular and well established configuration management tool that uses an expressive and powerful custom DSL based on Ruby to write provisioning scripts.
Thanks for learning with the DigitalOcean Community. Check out our offerings for compute, storage, networking, and managed databases.
Configuration management can drastically improve the integrity of servers over time by providing a framework for automating processes and keeping track of changes made to the system environment. This series will introduce you to the concepts behind Configuration Management and give you a practical overview of how to use Ansible, Puppet and Chef to automate server provisioning.


Dev/Ops passionate about open source, PHP, and Linux. Former Senior Technical Writer at DigitalOcean. Areas of expertise include LAMP Stack, Ubuntu, Debian 11, Linux, Ansible, and more. 
This textbox defaults to using to format your answer.
You can type in this text area to quickly search our full set of tutorials, documentation & marketplace offerings and insert the link!
It would’ve been great if you’d described steps of how to run your example playbook. That is the main purpose of tutorials to provide detailed instructions in order to readers could repeat the steps and see the results. Without such instructions it is just an overview of the tool and its capabilities.
It would be a great idea if you could explain how to run playbooks: in example ansible-playbooks -i playbook.yml
Tutorial is pretty good for Ansible playbooks ! But key point is missing, there is no speak about how to configure INI and how to execute Ansible scripts on your remote servers. For tutorial I think it is must have - how to execute it on your own server
How to run: In file add your IP address. Run this in your terminal: If u want run with specific user, after in file playbook.yml add remote_user: username
Hi good tutorial but needs updating to ansible 2.6 standard the code old pre 2.6 code

```
---
- hosts: all
  sudo: true
  vars:
     packages: [ 'vim', 'git', 'curl' ]
  tasks:
     - name: Install Package
       apt: name={{ item }} state=latest
       with_items: packages

```

```
---
- hosts: all
  become: true #same as sudo up

  vars:
      packages: ["vim", "git", "curl"] 
 #varables which in this case stores each package as an item within the array

  tasks:
    - name: installing packages on hosts 
      apt: name={{ item }} update_cache=yes state=latest
      with_items: "{{ packages }}" #calls the var packages
#but you can also call the pacakges in this manner
#      with_items:
#         - vim
#         - git
#         - curl # this is seen by ansible as "item": ["vim", "git", "curl"]

```

add v for verbosity and help with debugging it helps a lot if anyone knows of a good ansible linter please let me know as could use it to debug spacing issues
Could someone explain to me the templates part. I did not understand its syntax and what it is expected to do especially what is the ‘dest’ part for.
Thanks for this article Erika! The examples were good - everything worked for me, at least.
As an alternative, for anyone interested, you can setup two DigitalOcean droplets to play with Ansible - one to act as controller host and the other to serve as the node you’re controlling. Then just add the following
---
URL: https://spacelift.io/blog/ansible-best-practices
Conteúdo Extraído:
# 50+ Ansible Best Practices to Follow [Tips & Tricks]
Ansible is one of the most popular open-source software tools for configuration management, software provisioning, and application deployment of cloud or on-premises environments. This article will examine best practices for setting up Ansible projects and suggest approaches to deal with Ansible’s internals effectively. 
  1. Generic best practices and tips for Ansible project structure


If you are new to Ansible, take a look at this .
Quick tips for operating and configuring Ansible projects
  1. **Use Ansible Vault for secrets (or any other secrets management system)**
  2. In cloud environments, help you easily build your inventory and account for changes made to your infrastructure.
  3. Store your Ansible projects in Git for easy cycling through different versions.
  4. This process may seem hard, but if you are , you have an account-level overview of all the hosts that have been used in your Ansible workflows with Spacelift.
  5. **Combine provisioning and configuration in a single workflow:** Dynamic inventories are very powerful, but creating your inventory using IaC and then sharing it with Ansible can be really helpful in many situations. Spacelift lets you do this natively without having to write any code to pass the output from the IaC tool to the configuration management one.


## 1. Generic best practices and tips for Ansible project structure
In this section, we examine and discuss general best practices and recommendations for organizing your projects and getting the most out of Ansible.
Although Ansible allows JSON syntax, using YAML is preferred and improves the readability of files and projects. 
To separate things neatly and improve readability, consider leaving a blank line between blocks, tasks, or other components. 
because it enables more granular grouping and management of tasks. Tags allow us to add fine-grained controls to task execution. 
For further clarification, add a comment explaining the purpose and the reason behind plays, tasks, variables, etc.
Before setting up your Ansible projects, consider applying a consistent naming convention for your tasks (always name them), plays, variables, roles, and modules. 
Following a style guide encourages consistency. For inspiration, look at
You don’t have to use all of Ansible’s many options and advanced features. Find the Ansible parts and mechanics that fit your use case, and keep your Ansible projects as simple as possible. For example, begin with a simple playbook and static inventory and add more complex structures or refactor later according to your needs.
****– Store your projects in a Version Control System (VCS):**** Keep your Ansible files in a code repository and commit any new changes regularly.
instead of scattering custom modules and roles. Collections are now the main delivery format for roles, plugins, and modules.
for Python dependencies as first-class artifacts of your automation stack.
and add testing steps in your CI/CD pipelines for your Ansible repositories. For testing Ansible roles, look at . To test inputs or verify custom expressions, you can use the 
Here’s an example of a well-organized Ansible directory structure:

```
 
group_vars/
   group2.yml
host_vars/
  host2.yml
 
# Store here any custom module_utils to support modules (optional) 
 
roles/
#  <-- tasks file can include smaller files if warranted#  <-- files for use with the template resource#  <-- files for use with the copy resource#  <-- script files for use with the script resource#  <-- variables associated with this role#  <-- default lower priority variables for this role# or other types of plugins, like lookup in this case 
# same kind of structure as "common" was above, done for the monitoring role
```

Instead of relying on whatever Python is installed on your control node, package your Ansible runtime into a containerized  (EE) that includes ansible-core, collections, and system dependencies. This gives you reproducible automation across laptops, CI, and Spacelift workers.
Read more: 
Group hosts based on common attributes they might share (geography, purpose, roles, environment).
Define a separate inventory file per environment (production, staging, testing, etc.) to isolate them from each other and avoid mistakes by targeting the wrong environments.
**Dynamic inventory: When working with cloud providers and ephemeral or fast-changing environments, maintaining static inventories can become complex quickly. Set up a mechanism to synchronize the inventory dynamically with your cloud providers**
We can create dynamic groups using the `group_by` module based on a specific attribute. For example, group hosts dynamically based on their operating system and run different tasks on each without defining such groups in the inventory.

```
 
# tasks that only happen on Ubuntu go here    
# tasks that only happen on CentOS go here
```

**– Combine provisioning and configuration in a single workflow** – Dynamic inventories are very powerful, but creating your inventory using IaC and then sharing it with Ansible can be really helpful in many situations. Spacelift lets you do this natively, without having to write any code to pass the output from the IaC tool to the configuration management one:
Learn more about Ansible inventory: Working with Ansible Inventory – Basics and Use Cases.
In this section, we list and discuss best practices for using plays and playbooks — two basic components of Ansible projects.
To make your tasks more understandable, explicitly set the state parameter even though it might be unnecessary due to the default value.
**Place every task argument in its own separate line:** This point aligns with the general approach to striving for readability in our Ansible files. Check the examples below. 
Instead, use this syntax, which improves the readability and understandability of the tasks and their arguments:
**– Use top-level playbooks to orchestrate other lower-level playbooks:** You can logically group tasks, plays, and roles into low-level playbooks, use other top-level playbooks to import them, and set up an orchestration layer according to your needs. Refer to 
Tasks that relate to each other and share common attributes or tags can be grouped using the block option. Another advantage of this option is easier rollbacks for tasks under the same block.

```
 
 
 Copy the Nginx configuration file to the host
        
 Create link to the new config to enable it
 
 

```

**Use handlers for tasks that should be triggered:** allow a task to be executed after something has changed. This handler will be triggered when there are changes to index.html from the above example. 
Leading online gaming operator Novibet needed to expand its IaC capabilities to align with its ambitious growth strategy. The Spacelift platform has allowed the team to deploy faster and with more control as they advance toward a platform engineering mindset and enable autonomy with guardrails.
Variables allow users to parametrize different Ansible components and store values we can reuse throughout projects. Let’s look at some best practices and tips on using Ansible variables.
**– Always provide sane defaults for your variables:** Set default values for all groups under . For every role, set default role variables in .
To keep your inventory file clean, prefer setting group and hosts variables in the and directories.
**– Add the role name as a prefix to variables:** Try to be explicit when defining variable names for your roles by adding a prefix with the role name. 
It is not advisable to use all of the  unless you have specific needs. Pick the ones most appropriate for your use case and keep it as simple as possible.
**– Use double quotes for strings and single quotes for literal values** to avoid ambiguity and ensure that variables, strings, and other values are correctly interpreted.
How to Use Different Types of Ansible Variables
This section provides tips and best practices for using Ansible modules efficiently in tasks. 
Use each Ansible project’s directory to store relevant custom modules. Playbooks that have a directory relative to their path can directly reference any modules inside it.
Use and modules only when there isn’t another option. Instead, prefer specialized modules that provide idempotency and proper error handling. Read more about the .
**Specify module arguments when it makes sense: You can omit default values in many module arguments. To be more transparent and explicit, specify some of these arguments, like the**
**– Favor multi-tasks in a module over loops:** The most efficient way to define a list of similar tasks, like installing packages, is to use multiple tasks in a single module. 
Every custom module should include examples, explicitly document dependencies, and describe return responses. New modules should be tested thoroughly before release. You can create testing roles and playbooks to test your custom modules and validate different test cases. 
For more details about using modules and writing your own custom modules, check the Ansible Modules – How to Use Them Efficiently
enable reusability and efficient code sharing while providing a well-structured framework for configuring and setting projects. This section examines some best practices and tips for creating well-defined roles.
**– Follow the Ansible Galaxy Role Directory structure:** Leverage the command to generate a default role directory layout according to Ansible Galaxy’s standards.
Each role should have a separate responsibility and distinct functionality to conform with the separation of concerns design principle. Separate your roles based on different functionalities or technical domains. 
By avoiding many dependencies in your roles, you can keep them loosely coupled, develop them independently, and use them without managing complex dependencies between them.
Enhance control of the execution order of roles and tasks by using or over the classic option.
**– Do your due diligence for Ansible Galaxy Roles:** When downloading and using content and roles from Galaxy, do your due diligence, validate their content, and pick roles from trustworthy contributors.
To avoid depending on Ansible Galaxy’s upstream, you can store any roles from Galaxy in your code repositories and manage them as part of your project.


## 6. Execution and deployment best practices and tips
Ansible provides many controls and options to orchestrate execution against hosts. In this section, we explore tips and tricks for optimally controlling Ansible execution based on our needs.
Testing your tasks in a staging or testing environment before production is a great way to validate that your changes have the expected outcome.
flag 
**– Limit task execution to specific tasks based on tags:** If you need to run only specific tasks from a playbook based on tags, you can define the tags to be executed with the flag.
**– Validate which tasks will run before executing:** You can use the flag to confirm which tasks would be run without actually running them.
**Validate against which hosts the playbook will run:** You can use the flag to confirm which hosts will be affected by the playbook without running it.
**Validate which changes will happen without making them:** Leverage the flag to predict any changes that may occur. Combine it with flag to show differences in changed files.
Use the flag to start executing your playbook at a particular task.
**– Use rolling updates to control the number of target machines:** By default, Ansible attempts to run the play against all hosts in parallel. To achieve a rolling update setup, you can leverage the  keyword. Using this keyword, you can define the number of hosts to which the changes should be performed in parallel. 
By default, Ansible finishes the execution of each task on all hosts before moving to the next task. if you wish to select another execution strategy, 
**– Don’t store sensitive values in plain text:** For secrets and sensitive values, use  to encrypt variables and files and protect any sensitive information. 
This process may seem difficult, but if using Spacelift gives you an account-level overview of all the hosts that have been used in your Ansible workflows with Spacelift.
RBAC is always one of the most important aspects of security. For Ansible, this can be hard to implement, especially if you are not using a dedicated platform to run your workflows. Spacelift helps you with this by letting you define partial admin rights for your users:
Another important aspect of security for your Ansible workflows is to limit your privilege escalation, meaning that you should use the 
Implementing governance with policies to restrict certain tasks from running is another great security measure. Spacelift uses OPA for defining policies, so you can easily define fine-grained policies that restrict modules, enforce tagging, and more.
Scanning policies for security vulnerabilities ensures that you enforce best practices and are always up to speed regarding your configuration status. Spacelift integrates with any security vulnerability scanning tool and even lets you define custom policies for these tools, making it easy to make decisions for your runs.
and signed collections where available to ensure you don’t run tampered roles or modules in production.
Read more: Ansible Security Automation: Risks & 7 Best Practices
## Why use Spacelift to elevate your Ansible automation?
’s vibrant ecosystem and excellent GitOps flow can greatly assist you in managing and orchestrating Ansible. By introducing Spacelift on top of Ansible, you can easily create custom workflows based on pull requests and apply any necessary compliance checks for your organization.
  * – Manage the execution of Ansible playbooks from one central location.
  * – View all Ansible-managed hosts and related playbooks, with clear visual indicators showing the success or failure of recent runs.
  * – Audit Ansible playbook run results with detailed insights to pinpoint problems and simplify troubleshooting.
  * – Control what kind of resources engineers can create, what parameters they can have, how many approvals you need for a run, what kind of task you execute, what happens when a pull request is open, and where to send your notifications
  * – Build multi-infrastructure automation workflows with dependencies, having the ability to build a workflow that, for example, generates your EC2 instances using Terraform and combines it with Ansible to configure them
  * Creature comforts such as (reusable containers for your environment variables, files, and hooks), and the ability to run arbitrary code


If you want to learn more about using Spacelift with Ansible, check our , read our , or book a demo with one of our engineers.
Would you like to see this in action – or just want a tl;dr? Check out this video I put together showing you Spacelift’s new Ansible functionality:
In this blog post, we delved into best practices, tips, and tricks for operating and configuring Ansible projects. We explored approaches for structuring our Ansible projects and roles and set different configuration options regarding the inventory and variables. Lastly, we examined various tips for controlling our playbook’s execution and deployments. 
Managing large-scale playbook execution is hard. Spacelift enables you to automate Ansible playbook execution with visibility and control over resources, and seamlessly link provisioning and configuration workflows.

---
URL: https://www.pluralsight.com/courses/getting-started-ansible
Conteúdo Extraído:
What if you could specify WHAT a system should look like and another tool took care of making that possible so you don't need to know HOW it works and can focus on WHAT outcome is desired. That's what Ansible can do for you!
What if you could specify WHAT a system should look like and another tool took care of making that possible so you don't need to know HOW it works and can focus on WHAT outcome is desired. That's what Ansible can do for you!
Access this course and other top-rated tech content with one of our business plans.
Access this course and other top-rated tech content with one of our individual plans.
This course is included in the libraries shown below:
Ansible is a popular choice for IT automation because it allows you to concisely specify a desired state and then it does the heavy lifting to make that state a reality. In this course, Getting Started with Ansible, you will learn foundational knowledge to quickly and reliably configure just about anything with Ansible. First, you will learn how to install Ansible and use the ansible Ad-hoc command line tool to execute one-off modules in Ansible to configure single aspects of a system like ensuring a line exists in a file, or an application is installed. Playbooks will be composed of modules to build up larger configurations all stored in simple file(s) that pass through ansible-playbook. Then, you'll see how to use inventories to configure multiple machines including a full fledged VM learning lab that you then use Ansible to configure. Next, you'll explore how to learn what you need to know, when you need to know it. Later, you'll see how to swap out Ansible's default usage of SSH via connection plugins to connect to different environments such as Windows machines and docker containers. And how the ansible-pull command inverts Ansible's default push model. Finally, you'll discover reuse with Ansible Galaxy and corresponding ansible-galaxy command via both Roles and Collections. By the end of this course you'll be prepared to move beyond manually configuring applications, servers, networks, etc. Beyond writing confusing scripts. To spending your time on more valuable endeavors.
  * To view this content, start a free trial or activate one of our plans. 


  * To view this content, start a free trial or activate one of our plans. 
  * Using the git config Command to Manually Configure User Name and Email
To view this content, start a free trial or activate one of our plans. 
  * A Repeatable Script to Automatically Configure Git with user.name and user.email
To view this content, start a free trial or activate one of our plans. 
  * git config --add Is Not Idempotent Because It Duplicates Config
To view this content, start a free trial or activate one of our plans. 
  * Desired State Reconciliation and the Power of Ansible
To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * Know How to Know What You Need to Know as You Go
To view this content, start a free trial or activate one of our plans. 
  * Why Installs and Even Updates Are Easy - Control Node Architecture
To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * Disseminating a .gitconfig with Ansible Ad-hoc and the Copy Module
To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * How Ansible's Copy Module Handles Drift Thanks to Idempotence
To view this content, start a free trial or activate one of our plans. 
  * The --check Flag Simply Checks if Changes Would Be Made
To view this content, start a free trial or activate one of our plans. 
  * The --diff Flag Shows What Will Change or Did Change
To view this content, start a free trial or activate one of our plans. 


  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 


  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 


  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 


  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 


  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 
  * To view this content, start a free trial or activate one of our plans. 


Wes Higbee is passionate about helping companies achieve remarkable results with technology and software. He’s had extensive experience developing software and working with teams to improve how software is developed to meet business objectives. Wes launched Full City Tech to leverage his expertise to help companies delight customers.
More Courses by Wes
### 2025 Forrester Wave™ names Pluralsight as a among tech skills dev platforms 
See how our offering and strategy stack up.



---
URL: https://attuneops.io/top-5-ansible-alternatives/ [SCRAPE_FALHOU: crawl4ai_error]
Resumo (fallback): Ansibleis a server automation and configuration management tool that helps organizations maintain and manage large amounts of virtual and private servers. With it, you can automate repetitive tasks, deploy packages and applications simultaneously, and set up new servers. In this article, we will explore thealternativestoAnsibleand what ...
---
URL: https://spacelift.io/blog/ansible-alternatives [TRUNCADO]
Conteúdo Extraído:
# 13 Popular Ansible Alternatives You Should Know in 2026
Automation is very important in deploying and configuring your applications and infrastructure, streamlining repetitive tasks, reducing human error, and ensuring consistent environments.
Ansible plays a key role in automation, offering features like configuration management, task automation, application deployment, orchestration, cloud provisioning, and security compliance. Its use of YAML, a human-readable language, makes it accessible to users without programming experience. Additionally, Ansible doesn’t require specific agents on machines, keeping environments clean and organized. 
However, it’s not a universal solution; for more complex setups, tools like Chef, Puppet, or Terraform may be better suited.
Here are some of the top Ansible alternatives:
We aim to make our recommendations practical and vendor-neutral. For each tool we include, we evaluate category fit, core capabilities, integrations, documentation quality, security/governance features (when relevant), and pricing transparency. We also reference public review signals to validate common strengths and limitations.
Puppet is an open-source configuration management tool that uses a pull-based model to automate the deployment, configuration, and management of infrastructure across different operating systems. It operates on a master-agent architecture, where a central Puppet Master Server communicates with machines (or “nodes”) that have the Puppet Agent software installed.
Puppet uses a declarative language called the Puppet language. In this language, you define the desired state of your system in manifest files, specifying details like system resources, files, packages, and services. Puppet then compiles these manifests into catalogs, applies them to each node, and ensures the system’s state is correctly configured.
  * — You can deploy code numerous times on a system without affecting the desired state by getting the same result each time. This ensures the state of infrastructure always matches the desired state in the Puppet manifest file.
  * — The abstraction layer allows Puppet to easily manage resources across different operating systems and platforms, allowing Puppet to organize systems efficiently. 
  * — Puppet utilizes models to lay out dependencies and relationships between resources. This is useful when dealing with large environments. 
  * — The Puppet master controls the configuration information, and the Puppet agents retrieve the configuration from the master using a pull-based method. This becomes a more scalable solution for managing a large environment that has many nodes. 


Open-source (Apache 2.0) + Commercial version Puppet Enterprise  
|  : Mature and stable ecosystem that includes strong community support and documentation.  |  Puppet’s declarative language might be complex for beginners to learn. Initial Puppet infrastructure setup can also be time-consuming and require a lot of upfront configurations.   |  
| --- | --- |  
|  Modules cover a broad range of applications and services, enabling faster system deployments and configurations.   |  Managing agents across the board for the master-agent architecture can become tedious and introduces additional points of failure and complexity.   |  
|  Puppet master server requires heavy resources to be able to perform optimally.   |  
|  Puppet offers robust reporting and auditing capabilities that show detailed insights into the state of systems and the changes that were made, allowing admins to be compliant in regulated environments.   |  Latency in pull-based models can cause delays in configuration changes propagating from the master to the agent.   |  
|  Ease of managing multiple environments (DEV, QA, UAT, PROD) through the use of node classification and environment management, which allows admins to apply different configurations to different groups of nodes.   |  Admins don’t have immediate control over the configurations that are applied to the agent and cannot perform ad-hoc tasks because it follows a pull-based model.   |  
  * — Puppet’s primary use is , which ensures that all of your infrastructure is automated for configurations and applications and maintains uniformity across all of your servers. 
  * Puppet works well with IaC practices, allowing you to standardize and codify all of your infrastructure consistently. It can also automate server provisioning and more. 
  * — You can use it to automate application deployment and configurations across all applications hosted on your servers, reducing human error.
  * You can use Puppet in your CI/CD to automate your infrastructure and application deployment in your pipelines.
  * You can ensure systems and applications are up to date with the latest security patches and updates.
  * Puppet utilizes many security standards and policies to ensure compliance and maintain your security posture.
  * Automatically up and down from various changes in demand and traffic throughout your applications and servers.


due to its declarative language and master-agent setup, offering better control over complex systems that require detailed dependency modeling. It also excels at providing solid reporting and auditing, which is crucial for big operations.
thanks to its agentless architecture and use of YAML, a familiar language for beginners. Its push-based model allows for quicker deployments and real-time control, making it ideal for dynamic environments.
Ansible’s simplicity can sometimes be limiting, but it suits setups that prioritize ease of use and fast deployment. Although Puppet is more complex, it is better for environments that need precise control and compliance tracking.
Chef is an open-source configuration management tool that turns infrastructure into code, ensuring consistency, repeatability, and scalability in managing servers, applications, and services. Using Ruby-based “recipes” and “cookbooks,” users define the desired state of their nodes and automate the steps to achieve and maintain that state.
Chef follows a client-server model: Configurations are stored on the Chef Server, and the Chef Client, installed on managed nodes, pulls updates from the server. Admins test and update configurations locally before pushing them to the server using the ‘Knife’ tool.
Similar to Puppet, Chef supports CI/CD, version control, large-scale infrastructure, collaboration, and compliance, making it ideal for automating complex environments.
  * — Write, manage, and version control your infrastructure.
  * Utilize collection recipes, templates, files, and metadata that define the configuration and policy for your infrastructure. Recipes, written in Ruby, define the desired state of a node. 
  * — Store global variables, credentials, and other essential data in an encrypted or plain-text format using Chef Server’s data bags, ensuring secure storage and easy access for your recipes. 
  * Use Chef Supermarket for community-created cookbooks. Use the knife command-line tool to interact with the Supermarket and integrate these resources into your workflow.
  * Deploy the Chef Client on every node for management, while the Chef Server acts as the central repository for storing all cookbooks, policies, and node metadata.
  * Search tool in the Chef Server that allows you to retrieve information about nodes, data bags, cookbooks, etc. 
  * Use a Berksfile with Berkshelf to define and manage cookbook dependencies, simplifying cookbook sourcing and version control.

  
|  Utilizing Ruby you can achieve tailored solutions for specific needs.   |  You need a decent level of coding skills; it uses Ruby code with specific frameworks/conventions and Chef’s DSL (domain specific language).  Setting up a Chef Server and integrating it with existing infrastructure can be challenging and time consuming.   |  
| --- | --- |  
|  Chef enables codifying, versioning and collaborating to manage your infrastructure.  |  It is not feasible for environments that want to apply their changes on an ad-hoc basis.   |  
|  A strong community means you can use the Chef Supermarket to retrieve cookbooks created by peers.   |  Chef Client runs are resource-heavy, which can slow down your server’s performance.   |  
|  Chef allows you to test cookbooks and recipes in your workstation before pushing them to the Chef Server, using tools such as Test Kitchen, ChefSpec, InSpec, etc.  |  Chef relies heavily on the order of sequence for your instructions.  |  
|  You can ensure all nodes have configurations that are consistent across the board.   |   |  
  * Ensure all of your infrastructure is automated by defining and maintaining a desired state of servers and infrastructure components.
  * — Automate the provisioning of infrastructure components such as servers, containers and more.
  * — Simplify and standardize application deployment and configuration across multiple environments to ensure consistency and minimize manual errors.
  * — Integrate Chef into your CI/CD pipelines for automated testing, building, and deployment. 
  * Automatically update systems and applications with the latest security patches, ensuring your infrastructure remains secure and up-to-date.
  * — Enforce security standards and policies through automation to maintain compliance and strengthen your security posture.
  * — Design and execute complex workflows by orchestrating tasks across multiple nodes, enabling the efficient deployment and configuration of interconnected components.


Chef and Ansible are great tools for configuration management and automation, but they cater to different needs and use cases. Chef is ideal for environments prioritizing infrastructure as code, using a pull-based model, and supporting complex configurations through Ruby and Chef Server. This makes it a great choice for organizations needing scalable and consistent infrastructure management.
Chef’s pull-based model ensures nodes automatically check and apply updates, keeping environments consistent. With its agentless architecture and YAML-based configuration, Ansible, is easier for beginners. Its push-based model enables real-time control and faster deployments, which suits dynamic, fast-changing environments.
Chef can be considered an alternative to Ansible in scenarios where **obust configuration management, complex infrastructure automation, and desired-state enforcement**
Salt is a Python-based, open-source configuration management tool developed by SaltStack. It orchestrates, manages, and automates the configuration of servers, applications, and network devices. Salt uses a “master/minion” architecture, where the master server holds configurations and minions (clients) retrieve them. 
However, the key difference with Salt is that it has the capability of operating as an agentless tool (masterless), allowing you to use Salt’s configuration management for a single machine without calling out to a Salt master. This standalone option enables testing and operations independently of the master’s configurations. 
Salt uses “states” to ensure specific packages and services are properly set up. It employs the fast and secure ZeroMQ communication protocol for efficient, bi-directional communication between the master and minions. 
Salt supports both push and pull models and leverages Python for flexible configurations.
  *   * — Write, manage, and version control your infrastructure. 
  *   * — Set up complex workflows across various systems. 

  
|  Using the ZeroMQ high speed communication protocol, you increase scalability and speed between the master and minions.   |  Salt uses a complex feature set, which can get difficult to learn.  |  
| --- | --- |  
|  Salt can manage the state of your infrastructure in YAML, making it easy to understand.  |  Documentation is not well managed and updated. It can be challenging to follow through.   |  
|  You can choose either a pull or push model due to Salt’s agent/agentless architecture, increasing flexibility.  |  Salt does not work well with OSs other than Linux.   |  
|  Salt has the ability to execute commands remotely to systems, which is helpful when troubleshooting.  |  Salt requires significant resources to automate tasks efficiently and for optimal performance.  |  
|  Salt responds well to event triggers and ensures remediation and scaling are automated.   |  : The web UI lacks capabilities; you need to use command line for most tasks.   |  
|  generally easy to set up with an agent or agentless.  |  The flexibility and powerful features might introduce overhead in simpler environments.  |  
|  Salt has a well-rounded community with a library of modules and integrations available for your workflows.  |  
|   |  
  * Automate and standardize the configuration of servers and applications through Salt’s powerful, fast IaC features.
  * — Set up workflows across different systems and cloud providers, automating the full lifecycle. 
  * Set up triggers in your environment to automate specific tasks to respond to events that take place. 
  * Run commands and scripts on systems in real time. 


Salt is particularly suited to large, complex environments due to its high-speed communication with ZeroMQ, a feature few tools have. It also offers event-driven automation, which Ansible’s open-source version lacks. Additionally, Salt supports both push and pull models, providing flexibility in agent use. 
Security is another strength, as Salt uses its own key-store for agent communication, whereas Ansible relies on SSH. Ansible is more straightforward, but it struggles with complex workflows. 
Attune is an automation and orchestration tool designed for managing deployments, configurations, and workflows across various environments. It streamlines IT infrastructure management, using a pull-based model for consistency. 
Similar to Chef and Puppet, Attune uses a master-agent setup, with the server orchestrating tasks while managed machines require the Attune agent. It offers flexibility in scripting languages to automate workflow tasks. Attune’s intuitive interface and workflow-based approach simplify automation, making complex processes more manageable.
  * Allows you to create and manage complex workflows, enabling the automation of multi-step processes with ease
  * Ensure you can run workflows multiple times and produce the same outcome without unintended side effects, maintaining the desired state of the infrastructure 
  * — Utilizes a master-agent architecture, where the Attune server controls the tasks, and the agent carries out the task on the target nodes
  * Provides a user-friendly interface that simplifies the creation, management, and monitoring of automation workflows
  * — Can manage a wide range of operating systems and environments, offering flexibility and broad applicability

  
| Attune supports various languages in your automation, such as Python, Bash, Powershell, SQL, and more.  |  The initial setup and configuration may take time for new users to learn.   |  
| --- | --- |  
|  Attune simplifies workflow creation and management, reducing the complexity of automation tasks.  |  The Attune server might require significant resources to handle specific automation tasks efficiently.  |  
|  The master-agent architecture supports the management of large and complex environments.  |  requires the installation and maintenance of agents on all managed nodes, which can get messy.   |  
|  Attune ensures consistency and maintains desired infrastructure states across multiple executions.  |  This model is more unfavorable as it becomes difficult to perform ad-hoc tasks and click apply. Changes might not also be propagated instantly, due to the nature of the pull-based model.  |  
|  offers detailed insights into workflow execution and system states, assisting in compliance and auditing.  |  Setting up the Attune infrastructure can be time-consuming and requires specific upfront configuratio
---