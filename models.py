from datetime import datetime
from extensions import db


class ParkingSlot(db.Model):
    __tablename__ = "parking_slots"

    id = db.Column(db.Integer, primary_key=True)
    slot_number = db.Column(db.String(10), unique=True, nullable=False)
    slot_type = db.Column(db.String(20), default="regular")  # regular, handicap, vip
    is_occupied = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vehicles = db.relationship("Vehicle", backref="slot", lazy=True)

    def __repr__(self):
        return f"<ParkingSlot {self.slot_number}>"

    def to_dict(self):
        current = None
        for v in self.vehicles:
            if v.exit_time is None:
                current = v
                break
        return {
            "id": self.id,
            "slot_number": self.slot_number,
            "slot_type": self.slot_type,
            "is_occupied": self.is_occupied,
            "current_vehicle": current.to_dict() if current else None,
        }


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    license_plate = db.Column(db.String(20), nullable=False)
    vehicle_type = db.Column(db.String(20), default="car")  # car, bike, truck
    owner_name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    slot_id = db.Column(db.Integer, db.ForeignKey("parking_slots.id"), nullable=False)
    entry_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    exit_time = db.Column(db.DateTime, nullable=True)
    fee_charged = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Vehicle {self.license_plate}>"

    def duration_hours(self):
        end = self.exit_time if self.exit_time else datetime.utcnow()
        delta = end - self.entry_time
        return round(delta.total_seconds() / 3600, 2)

    def calculate_fee(self, hourly_rate=30.0, daily_max=300.0):
        hours = self.duration_hours()
        days = int(hours // 24)
        remaining_hours = hours % 24
        fee = (days * daily_max) + (remaining_hours * hourly_rate)
        return round(min(fee, days * daily_max + daily_max), 2)

    def to_dict(self):
        return {
            "id": self.id,
            "license_plate": self.license_plate,
            "vehicle_type": self.vehicle_type,
            "owner_name": self.owner_name,
            "phone": self.phone,
            "slot_id": self.slot_id,
            "slot_number": self.slot.slot_number if self.slot else None,
            "entry_time": self.entry_time.strftime("%Y-%m-%d %H:%M:%S") if self.entry_time else None,
            "exit_time": self.exit_time.strftime("%Y-%m-%d %H:%M:%S") if self.exit_time else None,
            "duration_hours": self.duration_hours(),
            "fee_charged": self.fee_charged,
            "is_active": self.is_active,
        }
