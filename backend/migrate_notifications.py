
import sqlite3

DB_PATH = "smartevent.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

try:
    cursor.execute("PRAGMA table_info(notifications)")
    columns = [column[1] for column in cursor.fetchall()]

    print("Existing columns:", columns)

    if "notification_type" not in columns:
        cursor.execute("""
            ALTER TABLE notifications
            ADD COLUMN notification_type VARCHAR(20)
            NOT NULL DEFAULT 'SYSTEM'
        """)
        print("Added notification_type column.")

    # Keep the legacy NOT NULL type column populated
    # when new notifications are inserted.
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS sync_notification_type_insert
        AFTER INSERT ON notifications
        WHEN NEW.type IS NULL OR NEW.type = ''
        BEGIN
            UPDATE notifications
            SET type = NEW.notification_type
            WHERE id = NEW.id;
        END;
    """)

    connection.commit()
    print("Migration completed.")

except Exception as error:
    connection.rollback()
    print("Migration failed:", repr(error))

finally:
    connection.close()
