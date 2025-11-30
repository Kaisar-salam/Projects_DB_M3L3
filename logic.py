import sqlite3
from config import DATABASE

skills = [ (_,) for _ in (['Python', 'SQL', 'API', 'Telegram'])]

statuses = [ (_,) for _ in (['На этапе проектирования', 'В процессе разработки', 'Разработан. Готов к использованию.', 'Обновлен', 'Завершен. Не поддерживается'])]

class DB_Manager:
    def __init__(self, database):
        self.database = database
        
    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE projects (
                            project_id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            project_name TEXT NOT NULL,
                            description TEXT,
                            url TEXT,
                            status_id INTEGER,
                            FOREIGN KEY(status_id) REFERENCES status(status_id)
                        )''') 
            conn.execute('''CREATE TABLE skills (
                            skill_id INTEGER PRIMARY KEY,
                            skill_name TEXT
                        )''')
            conn.execute('''CREATE TABLE project_skills (
                            project_id INTEGER,
                            skill_id INTEGER,
                            FOREIGN KEY(project_id) REFERENCES projects(project_id),
                            FOREIGN KEY(skill_id) REFERENCES skills(skill_id)
                        )''')
            conn.execute('''CREATE TABLE status (
                            status_id INTEGER PRIMARY KEY,
                            status_name TEXT
                        )''')
            conn.commit()

    def __executemany(self, sql, data):
        """Внутренняя функция для массового выполнения SQL."""
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(sql, data)
            conn.commit()
    
    def __select_data(self, sql, data = tuple()):
        """Внутренняя функция для SELECT запросов."""
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()
        
    def default_insert(self):
        """Заполняет таблицы навыков и статусов начальными значениями."""
        sql = 'INSERT OR IGNORE INTO skills (skill_name) values(?)'
        data = skills
        self.__executemany(sql, data)
        sql = 'INSERT OR IGNORE INTO status (status_name) values(?)'
        data = statuses
        self.__executemany(sql, data)


    def insert_project(self, data):
        """напишите данные в формате

            [(user_id, project_name, url, status_id)]
          description можно обновить позже через update_projects."""
        sql = """INSERT INTO projects 
            (user_id, project_name, url, status_id) 
            values(?, ?, ?, ?)"""
        self.__executemany(sql, data)


    def insert_skill(self, user_id, project_name, skill):
        """
        напишите данные в формате
        [(user_id, project_name, url, skill)]

        user_id — ID пользователя
        project_name — имя проекта
        skill — строка ('Python', 'SQL', 'API', 'Telegram')
        """
        sql = 'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?'
        project_id = self.__select_data(sql, (project_name, user_id))[0][0]
        skill_id = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill,))[0][0]
        data = [(project_id, skill_id)]
        sql = 'INSERT OR IGNORE INTO project_skills VALUES(?, ?)'
        self.__executemany(sql, data)


    def get_statuses(self):
        """Возвращает список всех статусов."""
        sql="SELECT status_name from status"
        return self.__select_data(sql)
        

    def get_status_id(self, status_name):
        """Возвращает id статуса по имени."""
        sql = 'SELECT status_id FROM status WHERE status_name = ?'
        res = self.__select_data(sql, (status_name,))
        if res: return res[0][0]
        else: return None

    def get_projects(self, user_id):
        """
        Возвращает все проекты пользователя.
        user_id — int
        """
        sql="""SELECT * FROM projects 
                WHERE user_id = ?"""
        return self.__select_data(sql, data = (user_id,))
        
    def get_project_id(self, project_name, user_id):
        """Возвращает ID проекта."""
        return self.__select_data(sql='SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?  ', data = (project_name, user_id,))[0][0]
        
    def get_skills(self):
        """Возвращает все доступные навыки."""
        return self.__select_data(sql='SELECT * FROM skills')
    
    def get_project_skills(self, project_name):
        """Возвращает список навыков проекта в виде строки."""
        res = self.__select_data(sql='''SELECT skill_name FROM projects 
                        JOIN project_skills ON projects.project_id = project_skills.project_id 
                        JOIN skills ON skills.skill_id = project_skills.skill_id 
                        WHERE project_name = ?''', data = (project_name,) )
        return ', '.join([x[0] for x in res])
    
    def get_project_info(self, user_id, project_name):
        """Возвращает подробную информацию о проекте."""
        sql = """
            SELECT project_name, description, url, status_name FROM projects 
            JOIN status ON
            status.status_id = projects.status_id
            WHERE project_name=? AND user_id=?
            """
        return self.__select_data(sql=sql, data = (project_name, user_id))


    def update_projects(self, param, data):
        """
        Обновляет одно поле проекта.

        ПЕРЕДАВАЙТЕ data В ФОРМАТЕ:
        data = (new_value, project_name, user_id)

        param может быть:
        'project_name', 'description', 'url', 'status_id'
        """
        sql = f"""UPDATE projects SET {param} = ? 
            WHERE project_name = ? AND user_id = ?"""
        self.__executemany(sql, [data]) 


    def delete_project(self, user_id, project_id):
        """
        Удаляет проект.

        ПЕРЕДАВАЙТЕ data В ФОРМАТЕ:
        (user_id, project_id)
        """
        sql = """DELETE FROM projects 
            WHERE user_id = ? AND project_id = ? """
        self.__executemany(sql, [(user_id, project_id)])
    
    def delete_skill(self, project_id, skill_id):
        """
        Удаляет связь проект-навык.

        ПЕРЕДАВАЙТЕ data В ФОРМАТЕ:
        (skill_id, project_id)
        """
        sql = """DELETE FROM skills 
            WHERE skill_id = ? AND project_id = ? """
        self.__executemany(sql, [(skill_id, project_id)])

    def clear_tables(self):
        """Удаляет все таблицы из базы данных."""
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('DROP TABLE IF EXISTS project_skills')
            conn.execute('DROP TABLE IF EXISTS projects')
            conn.execute('DROP TABLE IF EXISTS skills')
            conn.execute('DROP TABLE IF EXISTS status')
            conn.commit()
    
    def reset_db(self):
        """Удаляет все таблицы и создает их заново с начальными данными."""
        self.clear_tables()
        self.create_tables()
        self.default_insert()

if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    


    