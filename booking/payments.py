# Payment policy: Option B, No Hold / First Paid First Confirmed.
# Availability does not guarantee a reservation.
# The bot must never say a booking is reserved before payment is verified.

BOOKING_STAGES = [
    "Enquiry",
    "Availability Checked",
    "Awaiting Payment",
    "Payment Receipt Submitted",
    "Availability Rechecked",
    "Payment Verified",
    "Confirmed",
]


def submit_payment_receipt(booking_reference, receipt_image_url):
    """Phase 3/5 work. Marks a booking as Payment Receipt Submitted and
    notifies staff for manual verification. Does not confirm anything
    itself, staff make the final confirmation call.
    """
    raise NotImplementedError("Payment workflow not yet built, see Phase 3 in project plan.")


def recheck_availability_before_confirming(booking_reference):
    """Phase 3 work. Since there is no hold, availability must be rechecked
    at the moment a payment receipt is submitted, in case another customer
    booked the same slot first.
    """
    raise NotImplementedError("Payment workflow not yet built, see Phase 3 in project plan.")
