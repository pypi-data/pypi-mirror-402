from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime
import logging

# Configure logging to reduce noise
logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP("Demo: Elicitation MCP Server")


class ElicitationSchema:
    """Schema definitions for different elicitation types."""

    class GetDate(BaseModel):
        date: str = Field(
            description="Enter the date for your booking (YYYY-MM-DD)",
            pattern=r"^\d{4}-\d{2}-\d{2}$"
        )

    class GetPartySize(BaseModel):
        party_size: int = Field(
            description="Enter the number of people for your booking",
            ge=1,
            le=20
        )

    class ConfirmBooking(BaseModel):
        confirm: bool = Field(description="Confirm the booking")
        notes: str = Field(default="", description="Special requests or notes")


def validate_date(date_str: str) -> bool:
    """Validate date format and ensure it's not in the past."""
    try:
        booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        return booking_date >= datetime.now().date()
    except ValueError:
        return False


@mcp.tool()
async def book_table(ctx: Context, date: str = "", party_size: int = 0, confirm: bool = False, notes: str = "") -> str:
    """Book a table with intelligent elicitation for missing or invalid data.

    Args:
        date: The date for booking in YYYY-MM-DD format
        party_size: Number of people for the booking (1-20)
        confirm: Whether to confirm the booking
        notes: Special requests or notes for the booking

    Returns:
        Booking confirmation message
    """

    try:
        # Validate date if provided
        if date and not validate_date(date):
            return f"❌ Invalid date '{date}'. Please enter a valid future date in YYYY-MM-DD format."

        # Validate party size if provided
        if party_size and (party_size < 1 or party_size > 20):
            return f"❌ Invalid party size '{party_size}'. Party size must be between 1 and 20."

        # Check if all required parameters are provided
        if not date:
            return "❌ Date is required. Please provide the date in YYYY-MM-DD format."

        if not party_size:
            return "❌ Party size is required. Please provide the number of people (1-20)."

        # Process booking
        if confirm:
            notes_text = f" Notes: {notes}" if notes else ""
            return (f"✅ Your table for {party_size} people on {date} "
                    f"has been booked.{notes_text}")
        else:
            return "❌ Booking cancelled."

    except Exception as e:
        return f"❌ Booking failed due to unexpected error: {str(e)}"


def main():
    """Main entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()