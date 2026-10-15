
import { useEffect, useState } from "react";
import api from "../api";
import { useParams, useNavigate } from "react-router-dom";

function EventDetails() {
  const { event_id } = useParams();
  const navigate = useNavigate();

  // Event states
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [bookingLoading, setBookingLoading] = useState(false);

  // Module 18: Live ticket availability
  const [availability, setAvailability] = useState(null);
  const [availabilityLoading, setAvailabilityLoading] = useState(true);
  const [availabilityError, setAvailabilityError] = useState("");

  // Module 20: Wishlist
  const [wishlistSaved, setWishlistSaved] = useState(false);
  const [wishlistLoading, setWishlistLoading] = useState(false);

  // Module 21: Event updates
  const [eventUpdates, setEventUpdates] = useState([]);
  const [updatesError, setUpdatesError] = useState("");

  // Review states
  const [reviews, setReviews] = useState([]);
  const [averageRating, setAverageRating] = useState(0);
  const [totalReviews, setTotalReviews] = useState(0);
  const [rating, setRating] = useState(0);
  const [reviewText, setReviewText] = useState("");
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewError, setReviewError] = useState("");
  const [reviewMessage, setReviewMessage] = useState("");
  const [editingReviewId, setEditingReviewId] = useState(null);

  // Logged-in user ID
  const currentUserId = Number(localStorage.getItem("user_id"));

 
  // MODULE 19: Track viewed events for personalized recommendations
  useEffect(() => {
    const token = localStorage.getItem("token");

    // Only track views for logged-in users
    if (!token || !event_id) {
      return;
    }

    const trackEventView = async () => {
      try {
        await api.post(`/events/${event_id}/view`);
      } catch (error) {
        console.error("Unable to track event view:", error);
      }
    };

    trackEventView();
  }, [event_id]);


  // Fetch event details
  useEffect(() => {
    let cancelled = false;

    const fetchEvent = async () => {
      setLoading(true);

      try {
        const response = await api.get(`/events/${event_id}`);

        if (!cancelled) {
          setEvent(response.data);
        }
      } catch (error) {
        console.error("Error fetching event:", error);

        if (!cancelled) {
          setEvent(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchEvent();

    return () => {
      cancelled = true;
    };
  }, [event_id]);

  // Module 18: Refresh ticket availability every 10 seconds
  useEffect(() => {
    let cancelled = false;

    const fetchAvailability = async () => {
      try {
        const response = await api.get(
          `/events/${event_id}/availability`
        );

        if (!cancelled) {
          setAvailability(response.data);
          setAvailabilityError("");
        }
      } catch (error) {
        console.error("Error fetching ticket availability:", error);

        if (!cancelled) {
          setAvailabilityError(
            "Unable to refresh availability. Please try again."
          );
        }
      } finally {
        if (!cancelled) {
          setAvailabilityLoading(false);
        }
      }
    };

    setAvailability(null);
    setAvailabilityLoading(true);
    setAvailabilityError("");

    fetchAvailability();

    const intervalId = setInterval(fetchAvailability, 10000);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [event_id]);

    // Module 18: Receive live ticket availability through WebSocket
  
  useEffect(() => {
    if (!event_id) return;

    let websocket;
    let reconnectTimer;
    let isActive = true;

    const connectWebSocket = () => {
      if (!isActive) return;

      websocket = new WebSocket(
        `ws://127.0.0.1:8000/ws/events/${event_id}/availability`
      );

      websocket.onopen = () => {
        console.log("Connected to live ticket availability.");
      };

      websocket.onmessage = (message) => {
        try {
          const data = JSON.parse(message.data);
          setAvailability(data);
          setAvailabilityError("");
          setAvailabilityLoading(false);
        } catch (error) {
          console.error("Unable to read live availability:", error);
        }
      };

      websocket.onerror = (error) => {
        console.error("Availability WebSocket error:", error);
      };

      websocket.onclose = () => {
        if (isActive) {
          reconnectTimer = setTimeout(connectWebSocket, 3000);
        }
      };
    };

    connectWebSocket();

    return () => {
      isActive = false;
      clearTimeout(reconnectTimer);

      if (websocket) {
        websocket.onclose = null;
        websocket.close();
      }
    };
  }, [event_id]);


  // Module 18: Keep selected quantity within available seats
  useEffect(() => {
    const availableValue =
      availability?.available_tickets ??
      availability?.available ??
      availability?.tickets_available;

    if (availableValue === undefined || availableValue === null) {
      return;
    }

    const remaining = Number(availableValue);

    if (!Number.isFinite(remaining)) {
      return;
    }

    if (remaining > 0 && quantity > remaining) {
      setQuantity(Math.min(remaining, 10));
    } else if (remaining === 0) {
      setQuantity(1);
    }
  }, [availability, quantity]);

  // Fetch reviews and average rating
  const fetchReviews = async () => {
    try {
      const response = await api.get(`/events/${event_id}/reviews`);

      setReviews(response.data.reviews || []);
      setAverageRating(response.data.average_rating || 0);
      setTotalReviews(response.data.total_reviews || 0);
      setReviewError("");
    } catch (error) {
      console.error("Error fetching reviews:", error);

      setReviewError(
        error.response?.data?.detail || "Could not load reviews."
      );
    }
  };

  useEffect(() => {
    fetchReviews();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [event_id]);

  // Module 20: Check whether this event is already in the wishlist
  useEffect(() => {
    let cancelled = false;

    const fetchWishlistStatus = async () => {
      if (!localStorage.getItem("token")) {
        setWishlistSaved(false);
        return;
      }

      try {
        const response = await api.get("/wishlist");
        const items = Array.isArray(response.data)
          ? response.data
          : [];

        if (!cancelled) {
          setWishlistSaved(
            items.some(
              (item) => Number(item.event_id) === Number(event_id)
            )
          );
        }
      } catch (error) {
        console.error("Unable to load wishlist status:", error);
      }
    };

    fetchWishlistStatus();

    return () => {
      cancelled = true;
    };
  }, [event_id]);

  // Module 20: Add or remove an event from the wishlist
  const handleWishlistToggle = async () => {
    if (!localStorage.getItem("token")) {
      alert("Please login to manage your wishlist.");
      navigate("/login");
      return;
    }

    try {
      setWishlistLoading(true);

      if (wishlistSaved) {
        await api.delete(`/wishlist/${event_id}`);
        setWishlistSaved(false);
      } else {
        await api.post("/wishlist", {
          event_id: Number(event_id),
        });
        setWishlistSaved(true);
      }
    } catch (error) {
      alert(
        error.response?.data?.detail ||
          "Unable to update your wishlist. Please try again."
      );
    } finally {
      setWishlistLoading(false);
    }
  };

  // Module 21: Fetch event updates and announcements
  useEffect(() => {
    let cancelled = false;

    const fetchEventUpdates = async () => {
      try {
        const response = await api.get(
          `/events/${event_id}/updates`
        );

        if (!cancelled) {
          setEventUpdates(
            Array.isArray(response.data) ? response.data : []
          );
          setUpdatesError("");
        }
      } catch (error) {
        console.error("Unable to load event updates:", error);

        if (!cancelled) {
          setUpdatesError("Unable to load event updates.");
        }
      }
    };

    fetchEventUpdates();

    return () => {
      cancelled = true;
    };
  }, [event_id]);

  // Book tickets and proceed to payment
  const handleBooking = async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      alert("Please login to book tickets.");
      navigate("/login");
      return;
    }

    if (availabilityLoading || availabilityError || !validAvailability) {
      alert("Ticket availability is not confirmed. Please try again.");
      return;
    }

    if (!event || quantity < 1) {
      alert("Please select a valid ticket quantity.");
      return;
    }

    const availableCount = Number(
      availability?.available_tickets ??
        availability?.available ??
        availability?.tickets_available
    );

    if (quantity > availableCount) {
      alert(
        `Only ${availableCount} ticket(s) are currently available.`
      );
      return;
    }

    if (availableCount <= 0) {
      alert("Sorry, this event is sold out.");
      return;
    }

    if (
      ["CANCELLED", "COMPLETED", "ONGOING"].includes(
        event.event_status
      )
    ) {
      alert("Booking is unavailable for this event.");
      return;
    }

    try {
      setBookingLoading(true);

      const response = await api.post("/bookings", {
        event_id: Number(event_id),
        ticket_quantity: Number(quantity),
      });

      const booking = response.data;

      if (!booking?.id) {
        throw new Error(
          "Booking was created without returning a booking ID."
        );
      }

      if (booking.booking_status !== "PENDING") {
        alert(
          `Booking created with status: ${booking.booking_status}. Please check your booking history.`
        );

        navigate("/booking-history");
        return;
      }

      navigate(`/payment-checkout?booking_id=${booking.id}`);
    } catch (error) {
      console.error("Error creating booking:", error);

      alert(
        error.response?.data?.detail ||
          error.message ||
          "Booking failed. Please try again."
      );
    } finally {
      setBookingLoading(false);
    }
  };

  // Submit a new review or update an existing review
  const handleReviewSubmit = async (e) => {
    e.preventDefault();

    const token = localStorage.getItem("token");

    if (!token) {
      alert("Please login to write a review.");
      navigate("/login");
      return;
    }

    if (rating < 1 || rating > 5) {
      setReviewError("Please select a rating from 1 to 5 stars.");
      return;
    }

    try {
      setReviewLoading(true);
      setReviewError("");
      setReviewMessage("");

      const reviewData = {
        rating: Number(rating),
        review_text: reviewText.trim() || null,
      };

      if (editingReviewId !== null) {
        await api.put(`/reviews/${editingReviewId}`, reviewData);
        setReviewMessage("Your review was updated successfully.");
      } else {
        await api.post(`/events/${event_id}/reviews`, reviewData);
        setReviewMessage("Your review was submitted successfully.");
      }

      setRating(0);
      setReviewText("");
      setEditingReviewId(null);

      await fetchReviews();
    } catch (error) {
      setReviewError(
        error.response?.data?.detail || "Could not save your review."
      );
    } finally {
      setReviewLoading(false);
    }
  };

  // Load an existing review into the form for editing
  const handleEditReview = (review) => {
    setEditingReviewId(review.id);
    setRating(Number(review.rating));
    setReviewText(review.review_text || "");
    setReviewError("");
    setReviewMessage("");

    window.scrollTo({
      top: document.body.scrollHeight,
      behavior: "smooth",
    });
  };

  // Delete an existing review
  const handleDeleteReview = async (reviewId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete your review?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setReviewError("");
      setReviewMessage("");

      await api.delete(`/reviews/${reviewId}`);

      setReviewMessage("Your review was deleted successfully.");

      if (Number(editingReviewId) === Number(reviewId)) {
        setEditingReviewId(null);
        setRating(0);
        setReviewText("");
      }

      await fetchReviews();
    } catch (error) {
      setReviewError(
        error.response?.data?.detail || "Could not delete your review."
      );
    }
  };

  // Cancel editing
  const cancelEditing = () => {
    setEditingReviewId(null);
    setRating(0);
    setReviewText("");
    setReviewError("");
    setReviewMessage("");
  };

  // Loading screen
  if (loading) {
    return <h2>Loading event...</h2>;
  }

  // Event not found
  if (!event) {
    return <h2>Event not found</h2>;
  }

  const status = event.event_status || "UPCOMING";
  const statusClass = status.toLowerCase();

  const availableValue =
    availability?.available_tickets ??
    availability?.available ??
    availability?.tickets_available;

  const availableCount =
    availableValue === undefined || availableValue === null
      ? null
      : Number(availableValue);

  const soldOut =
    availableCount !== null &&
    Number.isFinite(availableCount) &&
    availableCount <= 0;

  const validAvailability =
    availableCount !== null &&
    Number.isFinite(availableCount) &&
    availableCount >= 0;

  const canBook =
    !availabilityLoading &&
    !availabilityError &&
    validAvailability &&
    !soldOut &&
    !["CANCELLED", "ONGOING", "COMPLETED"].includes(status);

  const maxSelectableQuantity = validAvailability
    ? Math.min(10, availableCount)
    : 0;

  return (
    <div className="event-details">
      <button
        type="button"
        className="back-button"
        onClick={() => navigate("/home")}
      >
        ← Back to Events
      </button>

      {/* Event image */}
      {event.banner_image && (
        <img
          src={event.banner_image}
          alt={event.title}
          className="details-image"
        />
      )}

      <h1>{event.title}</h1>

      <span className={`event-status ${statusClass}`}>
        {status}
      </span>

      {status === "CANCELLED" && (
        <div className="cancellation-notice">
          <h3>Event Cancelled</h3>
          <p>
            This event has been cancelled. Ticket booking is
            unavailable for this event.
          </p>
        </div>
      )}

      {status === "COMPLETED" && (
        <p className="event-info-notice">
          This event has already been completed.
        </p>
      )}

      {status === "ONGOING" && (
        <p className="event-info-notice">
          This event is currently ongoing. Ticket booking is
          unavailable.
        </p>
      )}

      {/* Event information */}
      <p>{event.description}</p>

      <p>
        <strong>Category:</strong> {event.category}
      </p>

      <p>
        <strong>Location:</strong> {event.location}
      </p>

      <p>
        <strong>Date:</strong>{" "}
        {new Date(event.event_date).toLocaleString()}
      </p>

      <p className="details-price">₹{event.ticket_price}</p>

      {/* MODULE 18: LIVE TICKET AVAILABILITY */}
      <section className="live-availability">
        <h3>Live Ticket Availability</h3>

        {availabilityLoading ? (
          <p>Loading ticket availability...</p>
        ) : availabilityError ? (
          <p role="alert">{availabilityError}</p>
        ) : validAvailability ? (
          <>
            <p>
              Available tickets: <strong>{availableCount}</strong>
            </p>

            {soldOut && (
              <p role="status">
                Sold out — tickets are currently unavailable.
              </p>
            )}

            {!soldOut && availableCount <= 10 && (
              <p>Only {availableCount} ticket(s) left!</p>
            )}
          </>
        ) : (
          <p role="alert">Availability data is invalid.</p>
        )}

        <small>
          Ticket availability updates live when bookings change.
        </small>
      </section>

      {/* MODULE 20: WISHLIST */}
      <div className="wishlist-action">
        <button
          type="button"
          onClick={handleWishlistToggle}
          disabled={wishlistLoading}
        >
          {wishlistLoading
            ? "Updating Wishlist..."
            : wishlistSaved
            ? "♥ Remove from Wishlist"
            : "♡ Add to Wishlist"}
        </button>
      </div>

      {/* MODULE 21: EVENT UPDATES */}
      <section className="event-updates">
        <h2>Live Event Updates</h2>

        {updatesError ? (
          <p>{updatesError}</p>
        ) : eventUpdates.length === 0 ? (
          <p>No announcements have been posted for this event yet.</p>
        ) : (
          eventUpdates.map((update) => (
            <article
              key={update.id}
              className={
                update.is_important
                  ? "event-update important-update"
                  : "event-update"
              }
            >
              {update.is_important && (
                <strong>📢 Important Announcement</strong>
              )}

              <p>{update.message}</p>

              <small>
                {update.created_at
                  ? new Date(update.created_at).toLocaleString()
                  : ""}
              </small>
            </article>
          ))
        )}
      </section>

      {/* Ticket booking */}
      {canBook ? (
        <div className="booking-box">
          <h3>Book Tickets</h3>

          <label htmlFor="ticket-quantity">
            Number of Tickets:
          </label>

          <select
            id="ticket-quantity"
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
            disabled={bookingLoading || availabilityLoading || !canBook}
          >
            {Array.from(
              { length: maxSelectableQuantity },
              (_, index) => (
                <option key={index + 1} value={index + 1}>
                  {index + 1} {index === 0 ? "Ticket" : "Tickets"}
                </option>
              )
            )}
          </select>

          <p>
            <strong>Total Price:</strong>{" "}
            ₹{Number(event.ticket_price * quantity).toFixed(2)}
          </p>

          <button
            type="button"
            className="book-button"
            onClick={handleBooking}
            disabled={
              bookingLoading ||
              !canBook ||
              quantity > availableCount
            }
            aria-busy={bookingLoading}
          >
            {bookingLoading ? (
              <>
                <span
                  className="booking-spinner"
                  aria-hidden="true"
                ></span>
                Creating Booking...
              </>
            ) : (
              <>
                Proceed to Payment
                <span aria-hidden="true"> →</span>
              </>
            )}
          </button>
        </div>
      ) : (
        <p className="event-info-notice">
          Booking is currently unavailable.
        </p>
      )}

      {/* MODULE 14: REVIEWS AND RATINGS */}
      <section className="event-reviews">
        <h2>Event Reviews & Ratings</h2>

        {/* Average rating */}
        <div className="rating-summary">
          <h3>⭐ {Number(averageRating).toFixed(1)} / 5</h3>

          <p>
            Based on {totalReviews}{" "}
            {totalReviews === 1 ? "review" : "reviews"}
          </p>
        </div>

        {/* Review submission and editing form */}
        <form className="review-form" onSubmit={handleReviewSubmit}>
          <h3>
            {editingReviewId !== null
              ? "Edit Your Review"
              : "Write a Review"}
          </h3>

          <label>Choose your rating:</label>

          <div
            className="star-rating"
            role="group"
            aria-label="Rating"
          >
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                className={`star-button ${
                  star <= rating ? "selected" : ""
                }`}
                onClick={() => setRating(star)}
                aria-label={`${star} ${
                  star === 1 ? "star" : "stars"
                }`}
                aria-pressed={rating === star}
              >
                ★
              </button>
            ))}
          </div>

          <textarea
            value={reviewText}
            onChange={(e) => setReviewText(e.target.value)}
            placeholder="Share your experience (optional)..."
            maxLength={2000}
            rows={4}
          />

          <p className="review-character-count">
            {reviewText.length}/2000 characters
          </p>

          {reviewError && (
            <p className="review-error">{reviewError}</p>
          )}

          {reviewMessage && (
            <p className="review-success">{reviewMessage}</p>
          )}

          <div className="review-form-actions">
            <button
              type="submit"
              className="book-button"
              disabled={reviewLoading}
            >
              {reviewLoading
                ? "Saving..."
                : editingReviewId !== null
                ? "Update Review"
                : "Submit Review"}
            </button>

            {editingReviewId !== null && (
              <button
                type="button"
                className="back-button"
                onClick={cancelEditing}
              >
                Cancel Edit
              </button>
            )}
          </div>
        </form>

        {/* Display existing reviews */}
        <div className="reviews-list">
          <h3>What Attendees Say</h3>

          {reviews.length === 0 ? (
            <p>
              No reviews yet. Be the first to review this event!
            </p>
          ) : (
            reviews.map((review) => {
              const isOwnReview =
                Number(review.user_id) === currentUserId;

              return (
                <article className="review-card" key={review.id}>
                  <div className="review-card-header">
                    <strong>
                      {isOwnReview
                        ? "Your Review"
                        : `Attendee #${review.user_id}`}
                    </strong>

                    <span className="review-stars">
                      {"★".repeat(Number(review.rating))}
                      {"☆".repeat(5 - Number(review.rating))}
                    </span>
                  </div>

                  <p className="review-text">
                    {review.review_text ||
                      "No written feedback provided."}
                  </p>

                  <small>
                    {new Date(review.created_at).toLocaleString()}
                  </small>

                  {/* Only show actions for the review owner */}
                  {isOwnReview && (
                    <div className="review-card-actions">
                      <button
                        type="button"
                        onClick={() => handleEditReview(review)}
                      >
                        Edit
                      </button>

                      <button
                        type="button"
                        onClick={() => handleDeleteReview(review.id)}
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </article>
              );
            })
          )}
        </div>
      </section>
    </div>
  );
}

export default EventDetails;
