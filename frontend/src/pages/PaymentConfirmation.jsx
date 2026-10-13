
import { Link, useLocation } from "react-router-dom";
import "./PaymentConfirmation.css";

function PaymentConfirmation() {
  const location = useLocation();

  const payment = location.state?.payment;
  const booking = location.state?.booking;

  // Handle direct page access or a page refresh.
  if (!payment) {
    return (
      <div className="payment-confirmation">
        <div className="confirmation-card">
          <h1>Payment Details Unavailable</h1>

          <p>
            Payment details are not available on this page.
            Please check your booking history.
          </p>

          <Link
            to="/booking-history"
            className="confirmation-button"
          >
            Booking History
          </Link>

          <Link to="/home" className="secondary-button">
            Back to Home
          </Link>
        </div>
      </div>
    );
  }

  const success = payment.payment_status === "SUCCESS";

  return (
    <div className="payment-confirmation">
      <div className="confirmation-card">
        <div
          className={`confirmation-icon ${
            success ? "success-icon" : "failed-icon"
          }`}
        >
          {success ? "✓" : "✕"}
        </div>

        <h1>
          {success ? "Payment Successful!" : "Payment Failed"}
        </h1>

        <p>
          {success
            ? "Your payment was completed and your booking is confirmed."
            : "Your payment was not completed. Your booking remains pending."}
        </p>

        <div className="confirmation-details">
          <div>
            <span>Payment ID</span>
            <strong>{payment.id}</strong>
          </div>

          <div>
            <span>Booking ID</span>
            <strong>{payment.booking_id}</strong>
          </div>

          <div>
            <span>Amount</span>
            <strong>
              ₹{Number(payment.amount).toFixed(2)}
            </strong>
          </div>

          <div>
            <span>Payment Status</span>
            <strong>{payment.payment_status}</strong>
          </div>

          <div>
            <span>Transaction ID</span>
            <strong className="transaction-id">
              {payment.transaction_id || "Not generated"}
            </strong>
          </div>

          <div>
            <span>Booking Status</span>
            <strong>
              {booking?.booking_status ||
                (success ? "CONFIRMED" : "PENDING")}
            </strong>
          </div>
        </div>

        <div className="confirmation-actions">
          {success ? (
            <Link
              to="/tickets"
              className="confirmation-button"
            >
              View My Tickets
            </Link>
          ) : (
            <Link
              to={`/payment-checkout?booking_id=${payment.booking_id}`}
              className="confirmation-button"
            >
              Try Again
            </Link>
          )}

          <Link to="/home" className="secondary-button">
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}

export default PaymentConfirmation;
