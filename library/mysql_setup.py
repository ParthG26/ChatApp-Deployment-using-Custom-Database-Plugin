#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import os

def run_command(cmd):
    result=subprocess.run(cmd,shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE,text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def main():
    module=AnsibleModule(
        argument_spec=dict(
            db_name=dict(required=True),
            db_username=dict(required=True),
            db_password=dict(required=True),
        ),
        supports_check_mode=False
    )

    db_name=module.params['db_name']
    db_username=module.params['db_username']
    db_password=module.params['db_password']

    result=dict(changed=False,output=[])

    for pkg in ['python3-pymysql', 'mysql-server']:
        rc, err, out= run_command(f"apt install -y {pkg}")
        result['output'].append(out or err)

    run_command("systemctl enable mysql")
    run_command("systemctl start mysql")

    run_command("sed -i 's/^bind-address.*/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf")
    run_command("systemctl restart mysql")

    rc,out,err = run_command("mysql -u root -e \"SELECT User FROM mysql.user WHERE User='root';\"")
    if 'using password' not in err:
        run_command(f"mysql -u root -e \"ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{db_password}'; FLUSH PRIVILEGES;\"")

    run_command(f"mysql -u root -p{db_password} -e \"CREATE DATABASE IF NOT EXISTS {db_name};\"")

    run_command(f"mysql -u root -p{db_password} -e \"CREATE USER IF NOT EXISTS '{db_username}'@'%' IDENTIFIED BY '{db_password}';\"") 
    run_command(f"mysql -u root -p{db_password} -e \"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_username}'@'%'; FLUSH PRIVILEGES;\"")

    result['changed']=True
    module.exit_json(**result)

if __name__ == '__main__':
    main()

