
function EventCardSkeleton() {
  return (
    <article className="event-skeleton">
      <div className="skeleton-image"></div>

      <div className="skeleton-content">
        <div className="skeleton-line skeleton-title"></div>
        <div className="skeleton-line skeleton-description"></div>
        <div className="skeleton-line skeleton-description short"></div>

        <div className="skeleton-line skeleton-info"></div>
        <div className="skeleton-line skeleton-info short"></div>

        <div className="skeleton-footer">
          <div className="skeleton-line skeleton-price"></div>
          <div className="skeleton-button"></div>
        </div>
      </div>
    </article>
  );
}

export default EventCardSkeleton;
