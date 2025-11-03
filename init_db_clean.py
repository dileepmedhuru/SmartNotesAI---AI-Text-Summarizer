"""
Clean Database Initialization Script
Creates fresh database WITHOUT YouTube support
"""
from app import app, db
from models import User
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_clean_database():
    """Initialize clean database without YouTube fields"""
    try:
        with app.app_context():
            db_path = 'smartnotes.db'
            
            # Check if database exists
            if os.path.exists(db_path):
                logger.warning(f"Database file '{db_path}' already exists!")
                response = input("Do you want to DELETE it and create a fresh database? (yes/no): ").lower().strip()
                
                if response != 'yes':
                    logger.info("Operation cancelled.")
                    return False
                
                # Backup old database
                import shutil
                from datetime import datetime
                backup_name = f"smartnotes_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(db_path, backup_name)
                logger.info(f"✓ Backup created: {backup_name}")
                
                # Remove old database
                os.remove(db_path)
                logger.info("✓ Old database removed")
            
            logger.info("Creating fresh database tables...")
            
            # Create all tables
            db.create_all()
            
            logger.info("✓ Database tables created successfully!")
            
            # Create test admin user
            logger.info("\nCreating test admin user...")
            
            test_user = User(
                username='admin',
                email='admin@smartnotes.com'
            )
            test_user.set_password('admin123')
            
            db.session.add(test_user)
            db.session.commit()
            
            logger.info("✓ Test admin user created!")
            logger.info("=" * 60)
            logger.info("TEST USER CREDENTIALS:")
            logger.info("  Username: admin")
            logger.info("  Email: admin@smartnotes.com")
            logger.info("  Password: admin123")
            logger.info("=" * 60)
            
            # Verify table structure
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = inspector.get_columns('summary_history')
            column_names = [col['name'] for col in columns]
            
            logger.info("\nDatabase columns:")
            for col in column_names:
                logger.info(f"  - {col}")
            
            # Check for YouTube columns
            youtube_cols = ['video_id', 'video_duration', 'video_author', 'video_views']
            found_youtube = [col for col in youtube_cols if col in column_names]
            
            if found_youtube:
                logger.warning(f"⚠️  YouTube columns still present: {found_youtube}")
                logger.warning("Please update models.py with the clean version!")
                return False
            else:
                logger.info("\n✓ No YouTube columns found - database is clean!")
            
            logger.info("\nYou can now:")
            logger.info("1. Run 'python app.py' to start the server")
            logger.info("2. Visit http://localhost:5000/login")
            logger.info("3. Login with the admin credentials above")
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("SmartNotes AI - Clean Database Initialization")
    print("(Without YouTube Support)")
    print("=" * 60 + "\n")
    
    success = init_clean_database()
    
    if success:
        print("\n✓ Database initialization completed successfully!\n")
    else:
        print("\n✗ Database initialization failed. Check the errors above.\n")