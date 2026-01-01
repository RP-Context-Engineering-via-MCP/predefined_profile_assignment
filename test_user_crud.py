# test_user_crud.py

"""
Test script demonstrating User CRUD operations with authentication
Run: python test_user_crud.py
"""

import sys
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.user_service import UserService
from app.schemas.user_dto import UserCreateRequest, UserUpdateRequest, UserLoginRequest
from app.models.user import User, UserStatus, UserProfileMode


def print_user(user: User, title: str = "User"):
    """Helper to print user details"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"User ID:                    {user.user_id}")
    print(f"Username:                   {user.username}")
    print(f"Email:                      {user.email}")
    print(f"Status:                     {user.status.value}")
    print(f"Profile Mode:               {user.profile_mode.value}")
    print(f"Predefined Profile ID:      {user.predefined_profile_id}")
    print(f"Dynamic Profile ID:         {user.dynamic_profile_id}")
    print(f"Dynamic Profile Confidence: {user.dynamic_profile_confidence}")
    print(f"Dynamic Profile Ready:      {user.dynamic_profile_ready}")
    print(f"Fallback Profile ID:        {user.fallback_profile_id}")
    print(f"Fallback Reason:            {user.fallback_reason}")
    print(f"Created At:                 {user.created_at}")
    print(f"Last Active At:             {user.last_active_at}")


def test_crud():
    """Test CRUD operations with service layer"""
    db: Session = SessionLocal()
    service = UserService(db)

    try:
        # ===== CREATE USERS =====
        print("\n" + "="*60)
        print("TEST 1: CREATE USERS")
        print("="*60)
        
        user1_data = UserCreateRequest(
            username="johndoe",
            email="john.doe@example.com",
            password="SecurePass123",
            predefined_profile_id="profile_001",
            profile_mode="COLD_START",
            dynamic_profile_confidence=0.0,
            dynamic_profile_ready=False
        )
        user1 = service.create_user(user1_data)
        print_user(user1, "Created User 1 (johndoe)")
        user1_id = user1.user_id

        user2_data = UserCreateRequest(
            username="janesmith",
            email="jane.smith@example.com",
            password="StrongPass456",
            predefined_profile_id="profile_002",
            dynamic_profile_id="dynamic_001",
            profile_mode="HYBRID",
            dynamic_profile_confidence=0.75,
            dynamic_profile_ready=True
        )
        user2 = service.create_user(user2_data)
        print_user(user2, "Created User 2 (janesmith)")
        user2_id = user2.user_id

        user3_data = UserCreateRequest(
            username="bobwilson",
            email="bob.wilson@example.com",
            password="MyPass789",
            predefined_profile_id="profile_003",
            profile_mode="COLD_START"
        )
        user3 = service.create_user(user3_data)
        print_user(user3, "Created User 3 (bobwilson)")
        user3_id = user3.user_id

        # ===== TEST DUPLICATE USERNAME/EMAIL =====
        print("\n" + "="*60)
        print("TEST 2: DUPLICATE USERNAME/EMAIL VALIDATION")
        print("="*60)
        
        try:
            duplicate_user = UserCreateRequest(
                username="johndoe",  # Duplicate username
                email="different@example.com",
                password="TestPass123"
            )
            service.create_user(duplicate_user)
            print("✗ FAILED: Should have rejected duplicate username")
        except ValueError as e:
            print(f"✓ PASSED: Duplicate username rejected - {e}")

        try:
            duplicate_email = UserCreateRequest(
                username="differentuser",
                email="john.doe@example.com",  # Duplicate email
                password="TestPass123"
            )
            service.create_user(duplicate_email)
            print("✗ FAILED: Should have rejected duplicate email")
        except ValueError as e:
            print(f"✓ PASSED: Duplicate email rejected - {e}")

        # ===== AUTHENTICATE USER =====
        print("\n" + "="*60)
        print("TEST 3: USER AUTHENTICATION")
        print("="*60)
        
        # Successful login
        login_data = UserLoginRequest(
            username="johndoe",
            password="SecurePass123"
        )
        authenticated_user = service.authenticate_user(login_data)
        if authenticated_user:
            print(f"✓ PASSED: User '{authenticated_user.username}' authenticated successfully")
            print(f"  User ID: {authenticated_user.user_id}")
            print(f"  Email: {authenticated_user.email}")
        else:
            print("✗ FAILED: Authentication failed")

        # Failed login - wrong password
        wrong_login = UserLoginRequest(
            username="johndoe",
            password="WrongPassword123"
        )
        failed_auth = service.authenticate_user(wrong_login)
        if failed_auth is None:
            print("✓ PASSED: Wrong password rejected")
        else:
            print("✗ FAILED: Should have rejected wrong password")

        # Failed login - non-existent user
        nonexistent_login = UserLoginRequest(
            username="nonexistent",
            password="SomePass123"
        )
        failed_auth2 = service.authenticate_user(nonexistent_login)
        if failed_auth2 is None:
            print("✓ PASSED: Non-existent user rejected")
        else:
            print("✗ FAILED: Should have rejected non-existent user")

        # ===== READ BY ID =====
        print("\n" + "="*60)
        print("TEST 4: READ USER BY ID")
        print("="*60)
        
        retrieved_user = service.get_user_by_id(user1_id)
        print_user(retrieved_user, "Retrieved User 1 by ID")

        # ===== READ BY USERNAME =====
        print("\n" + "="*60)
        print("TEST 5: READ USER BY USERNAME")
        print("="*60)
        
        user_by_username = service.get_user_by_username("janesmith")
        print_user(user_by_username, "Retrieved User 2 by Username")

        # ===== READ BY EMAIL =====
        print("\n" + "="*60)
        print("TEST 6: READ USER BY EMAIL")
        print("="*60)
        
        user_by_email = service.get_user_by_email("jane.smith@example.com")
        print_user(user_by_email, "Retrieved User 2 by Email")

        # ===== LIST ALL USERS =====
        print("\n" + "="*60)
        print("TEST 7: LIST ALL USERS")
        print("="*60)
        
        all_users, total = service.list_users()
        print(f"\nTotal Users: {total}")
        for i, u in enumerate(all_users, 1):
            print(f"{i}. {u.username} ({u.email}) - Status: {u.status.value}")

        # ===== UPDATE USER =====
        print("\n" + "="*60)
        print("TEST 8: UPDATE USER")
        print("="*60)
        
        update_data = UserUpdateRequest(
            dynamic_profile_id="dynamic_002",
            profile_mode="DYNAMIC_ONLY",
            dynamic_profile_confidence=0.85,
            dynamic_profile_ready=True
        )
        updated_user = service.update_user(user1_id, update_data)
        print_user(updated_user, "Updated User 1")

        # ===== CHANGE PASSWORD =====
        print("\n" + "="*60)
        print("TEST 9: CHANGE PASSWORD")
        print("="*60)
        
        # Successful password change
        try:
            service.change_password(user1_id, "SecurePass123", "NewSecurePass999")
            print("✓ PASSED: Password changed successfully")
            
            # Verify new password works
            new_login = UserLoginRequest(
                username="johndoe",
                password="NewSecurePass999"
            )
            auth_result = service.authenticate_user(new_login)
            if auth_result:
                print("✓ PASSED: New password authentication successful")
            else:
                print("✗ FAILED: New password authentication failed")
        except ValueError as e:
            print(f"✗ FAILED: Password change failed - {e}")

        # Failed password change - wrong old password
        try:
            service.change_password(user1_id, "WrongOldPass123", "AnotherPass999")
            print("✗ FAILED: Should have rejected wrong old password")
        except ValueError as e:
            print(f"✓ PASSED: Wrong old password rejected - {e}")

        # ===== SUSPEND USER =====
        print("\n" + "="*60)
        print("TEST 10: SUSPEND USER")
        print("="*60)
        
        suspended_user = service.suspend_user(user3_id, "Policy violation")
        print_user(suspended_user, "Suspended User 3")
        
        # Try to authenticate suspended user
        suspended_login = UserLoginRequest(
            username="bobwilson",
            password="MyPass789"
        )
        suspended_auth = service.authenticate_user(suspended_login)
        if suspended_auth is None:
            print("✓ PASSED: Suspended user cannot authenticate")
        else:
            print("✗ FAILED: Suspended user should not be able to authenticate")

        # ===== ACTIVATE USER =====
        print("\n" + "="*60)
        print("TEST 11: ACTIVATE USER")
        print("="*60)
        
        activated_user = service.activate_user(user3_id)
        print_user(activated_user, "Activated User 3")
        
        # Verify user can now authenticate
        activated_login = UserLoginRequest(
            username="bobwilson",
            password="MyPass789"
        )
        activated_auth = service.authenticate_user(activated_login)
        if activated_auth:
            print("✓ PASSED: Activated user can authenticate")
        else:
            print("✗ FAILED: Activated user should be able to authenticate")

        # ===== ACTIVATE FALLBACK PROFILE =====
        print("\n" + "="*60)
        print("TEST 12: ACTIVATE FALLBACK PROFILE")
        print("="*60)
        
        fallback_user = service.activate_fallback_profile(
            user1_id,
            fallback_profile_id="fallback_001",
            reason="High drift detected - confidence dropped below threshold"
        )
        print_user(fallback_user, "User 1 with Fallback Activated")

        # ===== DEACTIVATE FALLBACK PROFILE =====
        print("\n" + "="*60)
        print("TEST 13: DEACTIVATE FALLBACK PROFILE")
        print("="*60)
        
        normal_user = service.deactivate_fallback_profile(user1_id)
        print_user(normal_user, "User 1 with Fallback Deactivated")

        # ===== SEARCH USERS =====
        print("\n" + "="*60)
        print("TEST 14: SEARCH USERS")
        print("="*60)
        
        search_results, search_total = service.list_users(search="jane")
        print(f"\nSearch Results for 'jane': {search_total} found")
        for user in search_results:
            print(f"  - {user.username} ({user.email})")

        search_results2, search_total2 = service.list_users(search="smith")
        print(f"\nSearch Results for 'smith': {search_total2} found")
        for user in search_results2:
            print(f"  - {user.username} ({user.email})")

        # ===== FILTER BY STATUS =====
        print("\n" + "="*60)
        print("TEST 15: FILTER BY STATUS")
        print("="*60)
        
        active_users, active_count = service.list_users(status="active")
        print(f"\nActive Users: {active_count}")
        for user in active_users:
            print(f"  - {user.username} ({user.email}) - Status: {user.status.value}")

        # ===== PAGINATION =====
        print("\n" + "="*60)
        print("TEST 16: PAGINATION")
        print("="*60)
        
        page1_users, page1_total = service.list_users(skip=0, limit=2)
        print(f"\nPage 1 (limit=2): Showing 2 of {page1_total} total")
        for user in page1_users:
            print(f"  - {user.username}")

        page2_users, page2_total = service.list_users(skip=2, limit=2)
        print(f"\nPage 2 (limit=2): Showing {len(page2_users)} of {page2_total} total")
        for user in page2_users:
            print(f"  - {user.username}")

        # ===== SOFT DELETE =====
        print("\n" + "="*60)
        print("TEST 17: SOFT DELETE USER")
        print("="*60)
        
        service.delete_user(user2_id, hard_delete=False)
        deleted_user = service.get_user_by_id(user2_id)
        print_user(deleted_user, "Soft Deleted User 2")
        
        # Verify deleted user cannot authenticate
        deleted_login = UserLoginRequest(
            username="janesmith",
            password="StrongPass456"
        )
        deleted_auth = service.authenticate_user(deleted_login)
        if deleted_auth is None:
            print("✓ PASSED: Deleted user cannot authenticate")
        else:
            print("✗ FAILED: Deleted user should not be able to authenticate")

        # ===== FINAL STATE =====
        print("\n" + "="*60)
        print("TEST 18: FINAL USER LIST")
        print("="*60)
        
        final_users, final_total = service.list_users()
        print(f"\nFinal Total Users (excluding deleted): {final_total}")
        for i, u in enumerate(final_users, 1):
            print(f"{i}. {u.username} ({u.email}) - Status: {u.status.value}, Mode: {u.profile_mode.value}")

        # ===== SUMMARY =====
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✓ Created: 3 users")
        print(f"✓ Authentication: Tested successful and failed logins")
        print(f"✓ Password Management: Changed and verified passwords")
        print(f"✓ Account Status: Suspended and activated users")
        print(f"✓ Profile Management: Activated and deactivated fallback profiles")
        print(f"✓ Search & Filter: Tested search and status filtering")
        print(f"✓ Pagination: Tested pagination")
        print(f"✓ Soft Delete: Deleted user (status change)")
        print(f"✓ Final Count: {final_total} active users")

        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60)

    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("="*60)
    print("USER CRUD & AUTHENTICATION TEST SUITE")
    print("="*60)
    print("Testing User Service Layer with:")
    print("  - User creation with username/password")
    print("  - Authentication (login)")
    print("  - Password management")
    print("  - Account status management")
    print("  - Profile management")
    print("  - Search, filter, and pagination")
    print("="*60)
    
    test_crud()