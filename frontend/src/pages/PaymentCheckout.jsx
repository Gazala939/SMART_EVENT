
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import "./PaymentCheckout.css";

const API_URL = "http://127.0.0.1:8000";

function PaymentCheckout() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const initialBookingId = searchParams.get("booking_id") || "";

  const [bookingId, setBookingId] = useState(initialBookingId);
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [paymentStatus, setPaymentStatus] = useState("SUCCESS");

  // Coupon states
  const [couponCode, setCouponCode] = useState("");
  const [couponResult, setCouponResult] = useState(null);
  const [couponLoading, setCouponLoading] = useState(false);
  const [couponError, setCouponError] = useState("");

  const token = localStorage.getItem("token");

  // Load a booking belonging to the logged-in user.
  async function fetchBooking(id) {
    if (!id || Number(id) < 1) {
      setBooking(null);
      setCouponResult(null);
      setError("Please enter a valid booking ID.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setBooking(null);
      setCouponResult(null);
      setCouponError("");
      setCouponCode("");

      const response = await axios.get(
        `${API_URL}/bookings/my-bookings`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const selectedBooking = response.data.find(
        (item) => item.id === Number(id)
      );

      if (!selectedBooking) {
        setError("Booking not found in your account.");
        return;
      }

      setBooking(selectedBooking);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load booking details."
      );
    } finally {
      setLoading(false);
    }
  }

  // Redirect users who are not logged in.
  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }

    if (initialBookingId) {
      fetchBooking(initialBookingId);
    }
  }, [initialBookingId, token, navigate]);

  // Apply coupon using the backend API.
  async function handleApplyCoupon() {
    if (!booking) {
      setCouponError("Please load a booking first.");
      return;
    }

    if (booking.booking_status !== "PENDING") {
      setCouponError("Coupons can only be applied to pending bookings.");
      return;
    }

    if (!couponCode.trim()) {
      setCouponError("Please enter a coupon code.");
      return;
    }

    try {
      setCouponLoading(true);
      setCouponError("");
      setCouponResult(null);

      const response = await axios.post(
        `${API_URL}/coupons/apply`,
        {
          coupon_code: couponCode.trim(),
          booking_id: booking.id,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.data.valid) {
        setCouponError(
          response.data.message || "This coupon is not valid."
        );
        return;
      }

      setCouponResult(response.data);
    } catch (err) {
      setCouponError(
        err.response?.data?.detail ||
          "Unable to apply coupon. Please try again."
      );
    } finally {
      setCouponLoading(false);
    }
  }

  // Process the simulated payment.
  async function handlePayment() {
    if (!booking) {
      setError("Please load a valid booking first.");
      return;
    }

    if (booking.booking_status !== "PENDING") {
      setError("Only pending bookings can be paid for.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await axios.post(
        `${API_URL}/payments`,
        {
          booking_id: booking.id,
          payment_method: "SIMULATED",
          simulate_status: paymentStatus,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const payment = response.data;

      navigate("/payment-confirmation", {
        state: {
          payment,
          booking: {
            ...booking,
            discount_amount:
              couponResult?.discount_amount ??
              booking.discount_amount ??
              0,
            final_amount:
              payment.amount ??
              couponResult?.final_amount ??
              booking.final_amount ??
              booking.total_price,
            booking_status:
              payment.payment_status === "SUCCESS"
                ? "CONFIRMED"
                : "PENDING",
          },
        },
      });
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Payment could not be processed."
      );
    } finally {
      setLoading(false);
    }
  }

  const originalAmount = Number(booking?.total_price || 0);

  const discountAmount = couponResult
    ? Number(couponResult.discount_amount || 0)
    : Number(booking?.discount_amount || 0);

  const finalAmount = couponResult
    ? Number(couponResult.final_amount)
    : booking?.final_amount != null &&
        Number(booking.final_amount) > 0
      ? Number(booking.final_amount)
      : originalAmount;

  return (
    <div className="payment-checkout">
      <div className="payment-card">
        <h1>Payment Checkout</h1>

        <p className="payment-subtitle">
          Review your booking and apply a coupon before payment.
        </p>

        <div className="booking-search">
          <label htmlFor="bookingId">Booking ID</label>

          <div className="booking-search-row">
            <input
              id="bookingId"
              type="number"
              min="1"
              value={bookingId}
              onChange={(e) => {
                setBookingId(e.target.value);
                setBooking(null);
                setCouponResult(null);
                setCouponError("");
                setCouponCode("");
                setError("");
              }}
              placeholder="Enter your pending booking ID"
            />

            <button
              type="button"
              onClick={() => fetchBooking(bookingId)}
              disabled={loading || !bookingId}
            >
              Load
            </button>
          </div>
        </div>

        {loading && <p>Loading...</p>}

        {error && (
          <p className="payment-error">{error}</p>
        )}

        {booking && (
          <>
            <div className="booking-summary">
              <h2>Booking Summary</h2>

              <div className="summary-row">
                <span>Booking ID</span>
                <strong>{booking.id}</strong>
              </div>

              <div className="summary-row">
                <span>Event ID</span>
                <strong>{booking.event_id}</strong>
              </div>

              <div className="summary-row">
                <span>Tickets</span>
                <strong>{booking.ticket_quantity}</strong>
              </div>

              <div className="summary-row">
                <span>Original Amount</span>
                <strong>₹{originalAmount.toFixed(2)}</strong>
              </div>
            </div>

            {booking.booking_status === "PENDING" && (
              <div className="coupon-section">
                <h2>Have a coupon?</h2>

                <div className="coupon-input-row">
                  <input
                    type="text"
                    value={couponCode}
                    onChange={(e) => {
                      setCouponCode(e.target.value.toUpperCase());
                      setCouponResult(null);
                      setCouponError("");
                    }}
                    placeholder="Enter coupon code"
                    aria-label="Coupon code"
                  />

                  <button
                    type="button"
                    onClick={handleApplyCoupon}
                    disabled={couponLoading || !couponCode.trim()}
                  >
                    {couponLoading ? "Applying..." : "Apply Coupon"}
                  </button>
                </div>

                {couponError && (
                  <p className="payment-error">{couponError}</p>
                )}

                {couponResult && (
                  <p className="coupon-success">
                    {couponResult.message}
                  </p>
                )}
              </div>
            )}

            <div className="booking-summary price-breakdown">
              <h2>Price Breakdown</h2>

              <div className="summary-row">
                <span>Original Amount</span>
                <strong>₹{originalAmount.toFixed(2)}</strong>
              </div>

              <div className="summary-row discount-row">
                <span>
                  Discount
                  {couponResult?.coupon_code
                    ? ` (${couponResult.coupon_code})`
                    : ""}
                </span>
                <strong>
                  −₹{discountAmount.toFixed(2)}
                </strong>
              </div>

              <div className="summary-row total-row">
                <span>Final Amount</span>
                <strong>₹{finalAmount.toFixed(2)}</strong>
              </div>

              <div className="summary-row">
                <span>Booking Status</span>
                <strong>{booking.booking_status}</strong>
              </div>
            </div>

            {booking.booking_status === "PENDING" ? (
              <>
                <label htmlFor="paymentStatus">
                  Simulated Payment Result
                </label>

                <select
                  id="paymentStatus"
                  value={paymentStatus}
                  onChange={(e) =>
                    setPaymentStatus(e.target.value)
                  }
                >
                  <option value="SUCCESS">
                    Successful payment
                  </option>
                  <option value="FAILED">
                    Failed payment
                  </option>
                </select>

                <p className="demo-notice">
                  Demo mode only. This does not charge real money.
                </p>

                <button
                  type="button"
                  className="pay-button"
                  onClick={handlePayment}
                  disabled={loading}
                >
                  {loading
                    ? "Processing..."
                    : `Pay ₹${finalAmount.toFixed(2)}`}
                </button>
              </>
            ) : (
              <p className="payment-error">
                This booking is not pending. Only pending bookings can be paid.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default PaymentCheckout;
