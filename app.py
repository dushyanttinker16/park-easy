from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from extensions import db
from models import ParkingSlot, Vehicle
from config import config


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_slots(app)

    # ─────────────────────────────────────────────────────────
    # DASHBOARD
    # ─────────────────────────────────────────────────────────
    @app.route("/")
    def index():
        total = ParkingSlot.query.count()
        occupied = ParkingSlot.query.filter_by(is_occupied=True).count()
        available = total - occupied
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_revenue = (
            db.session.query(db.func.sum(Vehicle.fee_charged))
            .filter(Vehicle.exit_time >= today_start, Vehicle.is_active == False)
            .scalar()
            or 0.0
        )
        total_revenue = (
            db.session.query(db.func.sum(Vehicle.fee_charged))
            .filter(Vehicle.is_active == False)
            .scalar()
            or 0.0
        )
        total_vehicles = Vehicle.query.filter_by(is_active=False).count()
        return render_template(
            "index.html",
            total=total,
            occupied=occupied,
            available=available,
            today_revenue=round(today_revenue, 2),
            total_revenue=round(total_revenue, 2),
            total_vehicles=total_vehicles,
            occupancy_pct=round((occupied / total * 100) if total else 0, 1),
        )

    # ─────────────────────────────────────────────────────────
    # PARKING GRID
    # ─────────────────────────────────────────────────────────
    @app.route("/parking")
    def parking():
        slots = ParkingSlot.query.order_by(ParkingSlot.slot_number).all()
        return render_template("parking.html", slots=slots)

    @app.route("/api/slots")
    def api_slots():
        slots = ParkingSlot.query.order_by(ParkingSlot.slot_number).all()
        return jsonify([s.to_dict() for s in slots])

    # ─────────────────────────────────────────────────────────
    # VEHICLE ENTRY
    # ─────────────────────────────────────────────────────────
    @app.route("/entry", methods=["GET", "POST"])
    def vehicle_entry():
        available_slots = ParkingSlot.query.filter_by(is_occupied=False).order_by(ParkingSlot.slot_number).all()
        if request.method == "POST":
            license_plate = request.form.get("license_plate", "").strip().upper()
            vehicle_type = request.form.get("vehicle_type", "car")
            owner_name = request.form.get("owner_name", "").strip()
            phone = request.form.get("phone", "").strip()
            slot_id = request.form.get("slot_id")

            if not license_plate:
                flash("License plate is required.", "danger")
                return redirect(url_for("vehicle_entry"))

            # Check duplicate active
            existing = Vehicle.query.filter_by(license_plate=license_plate, is_active=True).first()
            if existing:
                flash(f"Vehicle {license_plate} is already parked in slot {existing.slot.slot_number}.", "warning")
                return redirect(url_for("vehicle_entry"))

            slot = ParkingSlot.query.get(slot_id)
            if not slot or slot.is_occupied:
                flash("Selected slot is not available.", "danger")
                return redirect(url_for("vehicle_entry"))

            vehicle = Vehicle(
                license_plate=license_plate,
                vehicle_type=vehicle_type,
                owner_name=owner_name,
                phone=phone,
                slot_id=slot.id,
                entry_time=datetime.utcnow(),
                is_active=True,
            )
            slot.is_occupied = True
            db.session.add(vehicle)
            db.session.commit()
            flash(f"Vehicle {license_plate} parked in slot {slot.slot_number} successfully!", "success")
            return redirect(url_for("parking"))

        return render_template("entry.html", available_slots=available_slots)

    # ─────────────────────────────────────────────────────────
    # VEHICLE EXIT
    # ─────────────────────────────────────────────────────────
    @app.route("/exit", methods=["GET", "POST"])
    def vehicle_exit():
        if request.method == "POST":
            license_plate = request.form.get("license_plate", "").strip().upper()
            vehicle = Vehicle.query.filter_by(license_plate=license_plate, is_active=True).first()
            if not vehicle:
                flash(f"No active vehicle found with plate {license_plate}.", "danger")
                return redirect(url_for("vehicle_exit"))

            vehicle.exit_time = datetime.utcnow()
            vehicle.fee_charged = vehicle.calculate_fee(
                hourly_rate=app.config["PARKING_HOURLY_RATE"],
                daily_max=app.config["PARKING_DAILY_MAX"],
            )
            vehicle.is_active = False
            vehicle.slot.is_occupied = False
            db.session.commit()

            return render_template("exit_receipt.html", vehicle=vehicle)

        active_vehicles = Vehicle.query.filter_by(is_active=True).order_by(Vehicle.entry_time.desc()).all()
        return render_template("exit.html", active_vehicles=active_vehicles)

    # ─────────────────────────────────────────────────────────
    # VEHICLES LIST
    # ─────────────────────────────────────────────────────────
    @app.route("/vehicles")
    def vehicles():
        search = request.args.get("search", "").strip()
        status = request.args.get("status", "all")
        page = request.args.get("page", 1, type=int)

        query = Vehicle.query
        if search:
            query = query.filter(
                Vehicle.license_plate.ilike(f"%{search}%")
                | Vehicle.owner_name.ilike(f"%{search}%")
            )
        if status == "active":
            query = query.filter_by(is_active=True)
        elif status == "exited":
            query = query.filter_by(is_active=False)

        vehicles_page = query.order_by(Vehicle.entry_time.desc()).paginate(page=page, per_page=15, error_out=False)
        return render_template("vehicles.html", vehicles_page=vehicles_page, search=search, status=status)

    # ─────────────────────────────────────────────────────────
    # HISTORY
    # ─────────────────────────────────────────────────────────
    @app.route("/history")
    def history():
        page = request.args.get("page", 1, type=int)
        records = (
            Vehicle.query.filter_by(is_active=False)
            .order_by(Vehicle.exit_time.desc())
            .paginate(page=page, per_page=20, error_out=False)
        )
        return render_template("history.html", records=records)

    # ─────────────────────────────────────────────────────────
    # REPORTS
    # ─────────────────────────────────────────────────────────
    @app.route("/reports")
    def reports():
        # Revenue by day (last 7 days)
        from sqlalchemy import func, cast, Date
        daily_revenue = (
            db.session.query(
                cast(Vehicle.exit_time, Date).label("day"),
                func.sum(Vehicle.fee_charged).label("revenue"),
                func.count(Vehicle.id).label("count"),
            )
            .filter(Vehicle.is_active == False, Vehicle.exit_time != None)
            .group_by(cast(Vehicle.exit_time, Date))
            .order_by(cast(Vehicle.exit_time, Date).desc())
            .limit(7)
            .all()
        )
        # Vehicle type breakdown
        type_breakdown = (
            db.session.query(Vehicle.vehicle_type, func.count(Vehicle.id))
            .group_by(Vehicle.vehicle_type)
            .all()
        )
        total_revenue = db.session.query(func.sum(Vehicle.fee_charged)).filter(Vehicle.is_active == False).scalar() or 0
        avg_duration = db.session.query(func.avg(Vehicle.fee_charged)).filter(Vehicle.is_active == False).scalar() or 0

        return render_template(
            "reports.html",
            daily_revenue=daily_revenue,
            type_breakdown=type_breakdown,
            total_revenue=round(total_revenue, 2),
            avg_fee=round(avg_duration, 2),
        )

    # ─────────────────────────────────────────────────────────
    # API – Dashboard live stats
    # ─────────────────────────────────────────────────────────
    @app.route("/api/stats")
    def api_stats():
        total = ParkingSlot.query.count()
        occupied = ParkingSlot.query.filter_by(is_occupied=True).count()
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_revenue = (
            db.session.query(db.func.sum(Vehicle.fee_charged))
            .filter(Vehicle.exit_time >= today_start, Vehicle.is_active == False)
            .scalar()
            or 0.0
        )
        return jsonify(
            {
                "total": total,
                "occupied": occupied,
                "available": total - occupied,
                "occupancy_pct": round((occupied / total * 100) if total else 0, 1),
                "today_revenue": round(today_revenue, 2),
            }
        )

    # ─────────────────────────────────────────────────────────
    # DELETE VEHICLE RECORD (admin)
    # ─────────────────────────────────────────────────────────
    @app.route("/vehicle/delete/<int:vid>", methods=["POST"])
    def delete_vehicle(vid):
        v = Vehicle.query.get_or_404(vid)
        if v.is_active:
            v.slot.is_occupied = False
        db.session.delete(v)
        db.session.commit()
        flash("Vehicle record deleted.", "info")
        return redirect(url_for("vehicles"))

    return app


def seed_slots(app):
    """Create 50 parking slots if none exist."""
    if ParkingSlot.query.count() == 0:
        total = app.config.get("PARKING_TOTAL_SLOTS", 50)
        slots = []
        for i in range(1, total + 1):
            if i <= 2:
                s_type = "handicap"
            elif i <= 5:
                s_type = "vip"
            else:
                s_type = "regular"
            slots.append(ParkingSlot(slot_number=f"P{i:03d}", slot_type=s_type))
        db.session.bulk_save_objects(slots)
        db.session.commit()


if __name__ == "__main__":
    app = create_app("development")
    app.run(debug=True, host="0.0.0.0", port=5000)
