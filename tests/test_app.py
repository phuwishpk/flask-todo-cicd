import pytest
from app import create_app
from app.models import db, Todo

@pytest.fixture
def app():
    """Create and configure a test app instance"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner"""
    return app.test_cli_runner()

class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_endpoint(self, client):
        """Test health check returns 200"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'

class TestTodoAPI:
    """Test Todo CRUD operations"""
    
    def test_get_empty_todos(self, client):
        """Test getting todos when database is empty"""
        response = client.get('/api/todos')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 0
        assert data['data'] == []
    
    def test_create_todo(self, client):
        """Test creating a new todo"""
        todo_data = {
            'title': 'Test Todo',
            'description': 'This is a test todo'
        }
        response = client.post('/api/todos', json=todo_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == 'Test Todo'
        assert data['data']['completed'] is False
    
    def test_create_todo_without_title(self, client):
        """Test creating todo without title fails"""
        response = client.post('/api/todos', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    def test_get_todo_by_id(self, client, app):
        """Test getting a specific todo by ID"""
        # Create a todo first
        with app.app_context():
            todo = Todo(title='Test Todo', description='Test')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id
        
        response = client.get(f'/api/todos/{todo_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == 'Test Todo'
    
    def test_get_nonexistent_todo(self, client):
        """Test getting a todo that doesn't exist"""
        response = client.get('/api/todos/9999')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
    
    def test_update_todo(self, client, app):
        """Test updating a todo"""
        # Create a todo first
        with app.app_context():
            todo = Todo(title='Original Title')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id
        
        update_data = {
            'title': 'Updated Title',
            'completed': True
        }
        response = client.put(f'/api/todos/{todo_id}', json=update_data)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == 'Updated Title'
        assert data['data']['completed'] is True
    
    def test_delete_todo(self, client, app):
        """Test deleting a todo"""
        # Create a todo first
        with app.app_context():
            todo = Todo(title='To Be Deleted')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id
        
        response = client.delete(f'/api/todos/{todo_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify it's deleted
        response = client.get(f'/api/todos/{todo_id}')
        assert response.status_code == 404
    
    def test_get_all_todos(self, client, app):
        """Test getting all todos"""
        # Create multiple todos
        with app.app_context():
            todos = [
                Todo(title='Todo 1'),
                Todo(title='Todo 2'),
                Todo(title='Todo 3')
            ]
            db.session.add_all(todos)
            db.session.commit()
        
        response = client.get('/api/todos')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 3