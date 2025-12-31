from app import db, User

# Create admin user
admin = User(
    username="admin",
    email="admin@dalfoods.com",
    role="admin"
)
admin.set_password("your_secure_password")

db.session.add(admin)
db.session.commit()
print("Admin user created successfully!")
