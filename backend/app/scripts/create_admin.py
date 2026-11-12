import argparse
import getpass
import sys
from backend.app.core.database import SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.user import User, Role, Profile
from backend.app.api.deps import record_audit_log

def create_admin(email: str, full_name: str, password: str) -> None:
    db = SessionLocal()
    try:
        email = email.lower().strip()
        admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
        if not admin_role:
            admin_role = Role(name="ADMIN", description="Administrator with complete management privileges")
            db.add(admin_role)
            db.flush()

        existing_user = db.query(User).filter(User.email == email).first()
        hashed_password = get_password_hash(password)

        if existing_user:
            existing_user.password_hash = hashed_password
            existing_user.role_id = admin_role.id
            existing_user.is_active = True
            existing_user.is_verified = True
            if existing_user.profile:
                existing_user.profile.full_name = full_name
            else:
                profile = Profile(user_id=existing_user.id, full_name=full_name, preferred_language="en")
                db.add(profile)
            user_id = existing_user.id
            action = "ADMIN_UPDATED_VIA_CLI"
            print(f"[+] Existing user '{email}' promoted to ADMIN successfully.")
        else:
            new_user = User(
                email=email,
                password_hash=hashed_password,
                role_id=admin_role.id,
                is_active=True,
                is_verified=True
            )
            db.add(new_user)
            db.flush()

            profile = Profile(
                user_id=new_user.id,
                full_name=full_name,
                preferred_language="en"
            )
            db.add(profile)
            user_id = new_user.id
            action = "ADMIN_PROVISIONED_VIA_CLI"
            print(f"[+] New administrator '{email}' created successfully.")

        db.commit()

        record_audit_log(
            db=db,
            action=action,
            resource_type="USER",
            resource_id=user_id,
            details={"email": email, "full_name": full_name, "role": "ADMIN"}
        )
        print("[+] Audit log recorded.")
    except Exception as e:
        db.rollback()
        print(f"[!] Error creating admin: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Securely provision an administrator account for SURAKSHA AI.")
    parser.add_argument("--email", required=True, help="Administrator email address")
    parser.add_argument("--name", default="System Administrator", help="Administrator display name")
    parser.add_argument("--password", help="Administrator password (prompted securely if not provided)")

    args = parser.parse_args()

    pwd = args.password
    if not pwd:
        pwd = getpass.getpass("Enter administrator password (min 8 chars): ")
        pwd_confirm = getpass.getpass("Confirm administrator password: ")
        if pwd != pwd_confirm:
            print("[!] Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    if len(pwd) < 8:
        print("[!] Password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    create_admin(args.email, args.name, pwd)

