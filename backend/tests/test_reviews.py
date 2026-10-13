
def test_create_review(client, completed_event):
    response = client.post(
        f"/events/{completed_event.id}/reviews",
        json={"rating": 5, "review_text": "Excellent event!"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 5
    assert data["review_text"] == "Excellent event!"


def test_get_reviews(client, completed_event):
    create_response = client.post(
        f"/events/{completed_event.id}/reviews",
        json={"rating": 4, "review_text": "Very good event"}
    )

    assert create_response.status_code == 200

    response = client.get(
        f"/events/{completed_event.id}/reviews"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_reviews"] == 1
    assert data["average_rating"] == 4.0


def test_update_review(client, completed_event):
    create_response = client.post(
        f"/events/{completed_event.id}/reviews",
        json={"rating": 3, "review_text": "It was good"}
    )

    assert create_response.status_code == 200
    review_id = create_response.json()["id"]

    response = client.put(
        f"/reviews/{review_id}",
        json={
            "rating": 5,
            "review_text": "Actually, it was excellent!"
        }
    )

    assert response.status_code == 200
    assert response.json()["rating"] == 5


def test_delete_review(client, completed_event):
    create_response = client.post(
        f"/events/{completed_event.id}/reviews",
        json={"rating": 4, "review_text": "Good event"}
    )

    assert create_response.status_code == 200
    review_id = create_response.json()["id"]

    response = client.delete(f"/reviews/{review_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Review deleted successfully"


def test_cannot_review_without_confirmed_booking(
    client, db_session, completed_event
):
    from models import Booking

    db_session.query(Booking).filter(
        Booking.event_id == completed_event.id
    ).delete()
    db_session.commit()

    response = client.post(
        f"/events/{completed_event.id}/reviews",
        json={
            "rating": 5,
            "review_text": "Should not be accepted"
        }
    )

    assert response.status_code == 403
