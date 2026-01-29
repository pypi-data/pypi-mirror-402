from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from datetime import datetime, timezone
from sqlalchemy import DateTime
db = SQLAlchemy()

# Base class for all elements
class Element(db.Model):
    __tablename__ = 'elements'
    __table_args__ = {'schema': 'sfrs_component_database'}  
    id = db.Column(db.Integer, primary_key=True)
    
    element_name = db.Column(db.String(20), nullable=False)
    location_name = db.Column(db.String(20))
    is_detector = db.Column(db.Boolean, default=False)
    type = db.Column(db.String(25), nullable=False)  # Discriminator column
    
    __mapper_args__ = {
        'polymorphic_identity': 'element',
        'polymorphic_on': type
    }

    aperture = db.relationship(
        "Aperture",
        uselist=False,
        back_populates="element",
        cascade="all, delete-orphan"
    )

    plm = db.relationship(
        "Plm",
        uselist=False,
        back_populates="element",
        cascade="all, delete-orphan"
    )

    location = db.relationship(
        "Location",
        uselist=False,
        back_populates="element",
        cascade="all, delete-orphan"
    )

class Location(db.Model):
    __tablename__ = 'location'
    __table_args__ = {'schema': 'sfrs_component_database'}

    id = db.Column(db.Integer, primary_key=True)

    element_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.elements.id'),
        unique=True,
        nullable=False
    )

    d = db.Column(db.Float, nullable=True) #length of the element
    begin_s = db.Column(db.Float, nullable=True)
    center_s = db.Column(db.Float, nullable=True)
    end_s = db.Column(db.Float, nullable=True)

    center_s_relative_to_focal_plane = db.Column(db.Float, nullable=True)

    relative_to_gsi_begin_x = db.Column(db.Float, nullable=True)
    relative_to_gsi_begin_y = db.Column(db.Float, nullable=True)
    relative_to_gsi_begin_angle = db.Column(db.Float, nullable=True)
    
    relative_to_gsi_center_x = db.Column(db.Float, nullable=True)
    relative_to_gsi_center_y = db.Column(db.Float, nullable=True)
    relative_to_gsi_center_angle = db.Column(db.Float, nullable=True)
    
    relative_to_gsi_end_x = db.Column(db.Float, nullable=True)
    relative_to_gsi_end_y = db.Column(db.Float, nullable=True)
    relative_to_gsi_end_angle = db.Column(db.Float, nullable=True)
    
    relative_to_target_begin_x = db.Column(db.Float, nullable=True)
    relative_to_target_begin_y = db.Column(db.Float, nullable=True)
    relative_to_target_begin_angle = db.Column(db.Float, nullable=True)
    
    relative_to_target_center_x = db.Column(db.Float, nullable=True)
    relative_to_target_center_y = db.Column(db.Float, nullable=True)
    relative_to_target_center_angle = db.Column(db.Float, nullable=True)
    
    relative_to_target_end_x = db.Column(db.Float, nullable=True)
    relative_to_target_end_y = db.Column(db.Float, nullable=True)
    relative_to_target_end_angle = db.Column(db.Float, nullable=True)
    
    is_in_high_energy_branch = db.Column(db.Boolean, nullable=True, default=False)
    is_in_low_energy_branch = db.Column(db.Boolean, nullable=True, default=False)
    is_in_ring_branch = db.Column(db.Boolean, nullable=True, default=False)

    element = db.relationship("Element", back_populates="location")

    @classmethod
    def from_dict(cls, data, *, element_id):
        allowed_fields = {
            c.name for c in cls.__table__.columns
            if c.name not in {"id", "element_id"}
        }

        filtered = {k: v for k, v in data.items() if k in allowed_fields}

        return cls(element_id=element_id, **filtered)

class Plm(db.Model):
    __tablename__ = 'plm'
    __table_args__ = {'schema': 'sfrs_component_database'}

    id = db.Column(db.Integer, primary_key=True)

    element_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.elements.id'),
        unique=True,
        nullable=False
    )

    last_update = db.Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=True)

    plm_comp_cid=db.Column(db.String(15), unique=True, nullable=True)
    plm_comp_cid_desc=db.Column(db.String(50), nullable=True)
    plm_comp_cid_parent=db.Column(db.String(15), nullable=True)
    plm_comp_aid=db.Column(db.String(11), nullable=True)
    plm_comp_sid_desc=db.Column(db.String(50), nullable=True)
    plm_comp_psp=db.Column(db.String(50), nullable=True)
    plm_comp_manufact=db.Column(db.String(50), nullable=True)
    plm_comp_manufact_country=db.Column(db.String(50), nullable=True)
    plm_comp_status=db.Column(db.String(4), nullable=True)
    plm_comp_status_description=db.Column(db.String(50), nullable=True)
    plm_comp_location=db.Column(db.String(50), nullable=True)
    plm_comp_manufact_serial=db.Column(db.String(50), nullable=True)
    plm_comp_wp=db.Column(db.String(50), nullable=True)
    plm_comp_order_no=db.Column(db.String(50), nullable=True)
    plm_comp_edms=db.Column(db.String(50), nullable=True)
    plm_comp_contract_no=db.Column(db.String(50), nullable=True)
    #plm_comp_system_id=db.Column(db.String(50))

    plm_log_contact=db.Column(db.String(50), nullable=True)
    plm_log_width=db.Column(db.String(50), nullable=True)
    plm_log_weight=db.Column(db.String(50), nullable=True)
    plm_log_height=db.Column(db.String(50), nullable=True)
    plm_log_length=db.Column(db.String(50), nullable=True)
    plm_log_storage_cond=db.Column(db.String(50), nullable=True)
    plm_log_tariff_exempt=db.Column(db.String(50), nullable=True)
    plm_log_deliv_loc=db.Column(db.String(50), nullable=True)
    plm_log_deliv_date=db.Column(db.String(50), nullable=True)
    plm_log_maintenance=db.Column(db.String(50), nullable=True)
    plm_log_constr_loc=db.Column(db.String(50), nullable=True)
    plm_log_final_loc=db.Column(db.String(50), nullable=True)
    plm_log_install_date=db.Column(db.String(50), nullable=True)
    plm_log_tariff_no=db.Column(db.String(50), nullable=True)
    plm_log_goodsin_date=db.Column(db.String(50), nullable=True)

    element = db.relationship("Element", back_populates="plm")

class Aperture(db.Model):
    __tablename__ = 'apertures'
    __table_args__ = {'schema': 'sfrs_component_database'}

    id = db.Column(db.Integer, primary_key=True)

    element_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.elements.id'),
        unique=True,
        nullable=False
    )

    # "circle", "rectangle", "complex"
    shape_type = db.Column(db.String(20), nullable=False)

    # --------------- Circle ---------------
    radius = db.Column(db.Float, nullable=True)

    # --------------- Rectangle ---------------
    rect_width = db.Column(db.Float, nullable=True)
    rect_height = db.Column(db.Float, nullable=True)

    # --------------- Complex shape ---------------
    polygon_points = db.Column(db.JSON, nullable=True)

    element = db.relationship("Element", back_populates="aperture")

    @validates('shape_type')
    def validate_shape(self, key, value):
        if value not in ("circle", "rectangle", "octogon", "complex"):
            raise ValueError("shape_type must be one of: circle, rectangle, complex")
        return value

    @validates('radius', 'rect_width', 'rect_height', 'polygon_points')
    def validate_geometry(self, key, value):
        if self.shape_type == "circle" and key == "radius" and (value is None or value <= 0):
            raise ValueError("Circle aperture must have a positive radius")
        if self.shape_type == "rectangle" and key in ("rect_width", "rect_height") and (value is None or value <= 0):
            raise ValueError("Rectangle aperture must have positive width and height")
        if self.shape_type == "complex" and key == "polygon_points" and (not value or not isinstance(value, list)):
            raise ValueError("Complex aperture must have a list of polygon points")
        return value

    # ---------------- Helper method ----------------
    def get_profile(self):
        """Return a dict with the key geometry info depending on shape type."""
        if self.shape_type == "circle":
            return {"radius": self.radius}
        elif self.shape_type == "rectangle":
            return {"width": self.rect_width, "height": self.rect_height}
        elif self.shape_type == "complex":
            return {"points": self.polygon_points}
        else:
            return {}

class Multiplett(Element):
    __tablename__ = 'multipletts'
    __table_args__ = {'schema': 'sfrs_component_database'}
    
    id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.elements.id'),
        primary_key=True
    )

    steerer = db.relationship('Steerer', back_populates='multiplett', foreign_keys='Steerer.multiplett_id')
    quadrupoles = db.relationship('Quadrupole', back_populates='multiplett', foreign_keys='Quadrupole.multiplett_id')
    sextupoles = db.relationship('Sextupole', back_populates='multiplett', foreign_keys='Sextupole.multiplett_id')
    octupoles = db.relationship('Octupole', back_populates='multiplett', foreign_keys='Octupole.multiplett_id')

    __mapper_args__ = {
        'polymorphic_identity': 'multiplett'
    }

# Derived class for Dipole
class Dipole(Element):
    __tablename__ = 'dipoles'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    loc = db.Column(db.JSON, nullable=True)
    bends_right = db.Column(db.Boolean, nullable = True)
    is_superconducting = db.Column(db.Boolean, nullable = True)
    bending_angle = db.Column(db.Float, nullable = True)
    bending_radius = db.Column(db.Float, nullable=True)
    magnetic_measurements = db.Column(db.PickleType, nullable=True)
    BDL_max = db.Column(db.Float, nullable=True)
    nominal_current = db.Column(db.Float, nullable=True)
    __mapper_args__ = {
        'polymorphic_identity': 'dipole'
    }

class CryoFeedbox(Element):
    __tablename__ = 'cryo_feed_boxes'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    
    branch = db.Column(db.String(5), nullable=True)
    feedbox_class = db.Column(db.String(50), nullable=True)
    design_type = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(100), nullable=True)
    cryo_suffix = db.Column(db.String(50), nullable=True)
    aid = db.Column(db.String(50), nullable=True)
    cid = db.Column(db.String(50), nullable=True)
    room = db.Column(db.String(50), nullable=True)
    functional_location = db.Column(db.String(50), nullable=True)
    capillary = db.Column(db.String(50), nullable=True)
    capillary_cryo = db.Column(db.String(50), nullable=True)
    cabling = db.Column(db.String(50), nullable=True)
    cabling_cryo = db.Column(db.String(50), nullable=True)
    cdb_id = db.Column(db.String(50), nullable=True)
    cad_date = db.Column(db.String(50), nullable=True)

    # relations (only ONE allowed)
    multiplett_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.multipletts.id'),
        nullable=True
    )

    dipole_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.dipoles.id'),
        nullable=True
    )

    multiplett = db.relationship(
        'Multiplett',
        backref=db.backref('cryo_feedboxes', lazy='dynamic'),
        foreign_keys=[multiplett_id]
    )

    dipole = db.relationship(
        'Dipole',
        backref=db.backref('cryo_feedboxes', lazy='dynamic'),
        foreign_keys=[dipole_id]
    )

    __mapper_args__ = {
        'polymorphic_identity': 'cryo_feed_box'
    }

    @property
    def connected_element(self):
        return self.multiplett or self.dipole

    @classmethod
    def from_dict(cls, data):
        allowed_fields = {
            c.name for c in cls.__table__.columns
            if c.name not in {"id"}
        }

        filtered = {k: v for k, v in data.items() if k in allowed_fields}

        return cls(**filtered)

class ExperimentalChamber(Element):
    __tablename__ = 'experimental_chambers'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slots = db.Column(db.Integer, nullable=False) 
    focal_plane = db.Column(db.String(4), nullable = False)

    # Add relationships with cascade
    empty_detectors = db.relationship(
        "EmptyDetector",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="EmptyDetector.experimental_chamber_id"  # <-- specify FK explicitly
    )

    beam_catchers = db.relationship(
        "BeamCatcher", 
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="BeamCatcher.experimental_chamber_id"  # <-- specify FK explicitly
    )

    collimators = db.relationship(
        "Collimator",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="Collimator.experimental_chamber_id"  # <-- specify FK explicitly
    )
    target_wheels = db.relationship(
        "TargetWheel",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="TargetWheel.experimental_chamber_id"  # <-- specify FK explicitly
    )
    seetrams = db.relationship(
        "Seetram",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="Seetram.experimental_chamber_id"  # <-- specify FK explicitly
    )
    beam_stoppers = db.relationship(
        "BeamStopper",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="BeamStopper.experimental_chamber_id"  # <-- specify FK explicitly
    )
    profile_grids = db.relationship(
        "ProfileGrid",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="ProfileGrid.experimental_chamber_id"  # <-- specify FK explicitly
    )
    gem_tpcs = db.relationship(
        "GEMTPC",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="GEMTPC.experimental_chamber_id"  # <-- specify FK explicitly
    )
    horizontal_slits = db.relationship(
        "HorizontalSlit",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="HorizontalSlit.experimental_chamber_id"  # <-- specify FK explicitly
    )
    vertical_slits = db.relationship(
        "VerticalSlit",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="VerticalSlit.experimental_chamber_id"  # <-- specify FK explicitly
    )
    plastic_scintillators = db.relationship(
        "PlasticScintillator",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="PlasticScintillator.experimental_chamber_id"  # <-- specify FK explicitly
    )
    rotary_wedge_degraders = db.relationship(
        "RotaryWedgeDegrader",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="RotaryWedgeDegrader.experimental_chamber_id"  # <-- specify FK explicitly
    )
    slidable_wedge_degraders = db.relationship(
        "SlidableWedgeDegrader",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="SlidableWedgeDegrader.experimental_chamber_id"  # <-- specify FK explicitly
    )
    ladder_system_degraders = db.relationship(
        "LadderSystemDegrader",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="LadderSystemDegrader.experimental_chamber_id"  # <-- specify FK explicitly
    )
    musics = db.relationship(
        "Music",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="Music.experimental_chamber_id"  # <-- specify FK explicitly
    )

    diamond_detectors = db.relationship(
        "DiamondDetector",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="DiamondDetector.experimental_chamber_id"  # <-- specify FK explicitly
    )

    targets = db.relationship(
        "Target",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="Target.experimental_chamber_id"  # <-- specify FK explicitly
    )

    tofs = db.relationship(
        "Tof",
        back_populates="experimental_chamber",
        cascade="all, delete-orphan",
        foreign_keys="Tof.experimental_chamber_id"  # <-- specify FK explicitly
    )

    __mapper_args__ = {
        'polymorphic_identity': 'experimental_chamber'
    }

class EmptyDetector(Element):
    __tablename__ = 'empty_detectors'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)

    # Foreign key to the experimental chamber
    experimental_chamber_id = db.Column(
        db.Integer, 
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'), 
        nullable=True
    )

    # Disambiguated relationship
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='empty_detectors',
        foreign_keys=[experimental_chamber_id]
    )

    __mapper_args__ = {
        'polymorphic_identity': 'empty_detector'
    }

class BeamStopper(Element):
    __tablename__ = 'beam_stoppers'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    pneumatic_actuator = db.Column(db.String(15), nullable=False)

    # Foreign key to the experimental chamber
    experimental_chamber_id = db.Column(
        db.Integer, 
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'), 
        nullable=True
    )

    # Disambiguated relationship
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='beam_stoppers',
        foreign_keys=[experimental_chamber_id]
    )

    __mapper_args__ = {
        'polymorphic_identity': 'beam_stopper'
    }

class ProfileGrid(Element):
    __tablename__ = 'profile_grids'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    stepper_motor = db.Column(db.String(15), nullable=True) 
    # Foreign key to the experimental chamber
    experimental_chamber_id = db.Column(
        db.Integer, 
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'), 
        nullable=True
    )

    # Disambiguated relationship
    experimental_chamber = db.relationship(
        "ExperimentalChamber",
        back_populates="profile_grids",
        foreign_keys=[experimental_chamber_id]
    )
    __mapper_args__ = {
        'polymorphic_identity': 'profile_grid'
    }

class GEMTPC(Element):
    __tablename__ = 'gem_tpcs'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    stepper_motor = db.Column(db.String(15), nullable=True) 
    pneumatic_actuator = db.Column(db.String(15), nullable=True) 
    # Foreign key to the experimental chamber
    experimental_chamber_id = db.Column(
        db.Integer, 
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'), 
        nullable=True
    )

    # Disambiguated relationship
    experimental_chamber = db.relationship(
        "ExperimentalChamber",
        back_populates="gem_tpcs",
        foreign_keys=[experimental_chamber_id]
    )
    __mapper_args__ = {
        'polymorphic_identity': 'gem_tpc'
    }

class HorizontalSlit(Element):
    __tablename__ = 'horizontal_slits'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    left_slit = db.Column(db.String(15), nullable=False) 
    right_slit = db.Column(db.String(15), nullable=False) 
    # Foreign key to the experimental chamber
    experimental_chamber_id = db.Column(
        db.Integer, 
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'), 
        nullable=True
    )

    # Disambiguated relationship
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='horizontal_slits',
        foreign_keys=[experimental_chamber_id]   
    )
    __mapper_args__ = {
        'polymorphic_identity': 'horizontal_slit'
    }

class VerticalSlit(Element):
    __tablename__ = 'vertical_slits'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    upper_slit = db.Column(db.String(15), nullable=False) 
    lower_slit = db.Column(db.String(15), nullable=False) 
    # Foreign key to the experimental chamber
    experimental_chamber_id = db.Column(
        db.Integer, 
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'), 
        nullable=True
    )

    # Disambiguated relationship
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='vertical_slits',
        foreign_keys=[experimental_chamber_id]   
    )
    __mapper_args__ = {
        'polymorphic_identity': 'vertical_slit'
    }

class PlasticScintillator(Element):
    __tablename__ = 'plastic_scintillators'
    __table_args__ = {'schema': 'sfrs_component_database'}  
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    pneumatic_actuator = db.Column(db.String(15), nullable=False) 
    # Foreign key to the experimental chamber
    experimental_chamber_id = db.Column(
        db.Integer, 
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'), 
        nullable=True
    )

    # Disambiguated relationship
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='plastic_scintillators',
        foreign_keys=[experimental_chamber_id]   
    )
    __mapper_args__ = {
        'polymorphic_identity': 'plastic_scintillator'
    }

class RotaryWedgeDegrader(Element):
    __tablename__ = 'rotary_wedge_degraders'
    __table_args__ = {'schema': 'sfrs_component_database'}
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    stepper_motor = db.Column(db.String(15), nullable=False) 
    pneumatic_actuator = db.Column(db.String(15), nullable=False) 
    central_thickness = db.Column(db.Float, nullable=True)
    max_angle = db.Column(db.Float, nullable=True)
    material = db.Column(db.String(15), nullable=True) 
    
    # Foreign key to the experimental chamber
    experimental_chamber_id = db.Column(
        db.Integer, 
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'), 
        nullable=True
    )

    # Disambiguated relationship
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='rotary_wedge_degraders',
        foreign_keys=[experimental_chamber_id]   
    )
    __mapper_args__ = {
        'polymorphic_identity': 'rotary_wedge_degrader'
    }

class Tof(Element):
    __tablename__ = 'tofs'
    __table_args__ = {'schema': 'sfrs_component_database'}
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    stepper_motor = db.Column(db.String(15), nullable=False) 
    # Foreign key to the experimental chamber
    experimental_chamber_id = db.Column(
        db.Integer, 
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'), 
        nullable=True
    )

    # Disambiguated relationship
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='tofs',
        foreign_keys=[experimental_chamber_id]   
    )
    __mapper_args__ = {
        'polymorphic_identity': 'tof'
    }

class SlidableWedgeDegrader(Element):
    __tablename__ = 'slidable_wedge_degraders'
    __table_args__ = {'schema': 'sfrs_component_database'}  
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    stepper_motor = db.Column(db.String(15), nullable=False)

    material = db.Column(db.String(15), nullable=True) 
    min_thickness = db.Column(db.Float, nullable=True)
    max_thickness = db.Column(db.Float, nullable=True)


    # Foreign key to the experimental chamber
    experimental_chamber_id = db.Column(
        db.Integer, 
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'), 
        nullable=True
    )

    # Disambiguated relationship
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='slidable_wedge_degraders',
        foreign_keys=[experimental_chamber_id]   
    )
    __mapper_args__ = {
        'polymorphic_identity': 'slidable_wedge_degrader'
    }

class LadderSystemDegrader(Element):
    __tablename__ = 'ladder_system_degraders'
    __table_args__ = {'schema': 'sfrs_component_database'}
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    stepper_motor = db.Column(db.String(15), nullable=False)
    # Foreign key to the experimental chamber
    experimental_chamber_id = db.Column(
        db.Integer, 
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'), 
        nullable=True
    )

    # Disambiguated relationship
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='ladder_system_degraders',
        foreign_keys=[experimental_chamber_id]   
    )
    __mapper_args__ = {
        'polymorphic_identity': 'ladder_system_degrader'
    }

class Seetram(Element):
    __tablename__ = 'seetrams'
    __table_args__ = {'schema': 'sfrs_component_database'}
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    
    # Foreign key to the experimental chamber
    experimental_chamber_id = db.Column(
        db.Integer, 
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'), 
        nullable=True
    )

    # Disambiguated relationship
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='seetrams',
        foreign_keys=[experimental_chamber_id]   
    )
    __mapper_args__ = {
        'polymorphic_identity': 'seetram'
    }

class TargetWheel(Element):
    __tablename__ = 'target_wheels'
    __table_args__ = {'schema': 'sfrs_component_database'}
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    camera = db.Column(db.String(15), nullable=False)

    # Foreign key zur ExperimentalChamber
    experimental_chamber_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'),
        nullable=True
    )

    # Richtige Beziehung zu ExperimentalChamber
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='target_wheels',
        foreign_keys=[experimental_chamber_id]
    )

    __mapper_args__ = {
        'polymorphic_identity': 'target_wheel'
    }

class Collimator(Element):
    __tablename__ = 'collimators'
    __table_args__ = {'schema': 'sfrs_component_database'}
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)

    # Foreign key zur ExperimentalChamber
    experimental_chamber_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'),
        nullable=True
    )

    # Richtige Beziehung zu ExperimentalChamber
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='collimators',
        foreign_keys=[experimental_chamber_id]
    )

    __mapper_args__ = {
        'polymorphic_identity': 'collimator'
    }

class BeamCatcher(Element):
    __tablename__ = 'beam_catchers'
    __table_args__ = {'schema': 'sfrs_component_database'}
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)

    # Foreign key zur ExperimentalChamber
    experimental_chamber_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'),
        nullable=True
    )

    # Richtige Beziehung zu ExperimentalChamber
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='beam_catchers',
        foreign_keys=[experimental_chamber_id]
    )

    __mapper_args__ = {
        'polymorphic_identity': 'beam_catcher'
    }

class DiamondDetector(Element):
    __tablename__ = 'diamond_detectors'
    __table_args__ = {'schema': 'sfrs_component_database'}
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    stepper_motor = db.Column(db.String(15), nullable=True)

    # Foreign key zur ExperimentalChamber
    experimental_chamber_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'),
        nullable=True
    )

    # Richtige Beziehung zu ExperimentalChamber
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='diamond_detectors',
        foreign_keys=[experimental_chamber_id]
    )

    __mapper_args__ = {
        'polymorphic_identity': 'diamond_detector'
    }

class Target(Element):
    __tablename__ = 'targets'
    __table_args__ = {'schema': 'sfrs_component_database'}
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    stepper_motor = db.Column(db.String(15), nullable=False)

    # Foreign key zur ExperimentalChamber
    experimental_chamber_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'),
        nullable=True
    )

    # Richtige Beziehung zu ExperimentalChamber
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='targets',
        foreign_keys=[experimental_chamber_id]
    )

    __mapper_args__ = {
        'polymorphic_identity': 'target'
    }

class Music(Element):
    __tablename__ = 'musics'
    __table_args__ = {'schema': 'sfrs_component_database'}
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    slot_number = db.Column(db.Integer, nullable=True)
    pneumatic_actuator = db.Column(db.String(15), nullable=False)
    # Foreign key to the experimental chamber
    experimental_chamber_id = db.Column(
        db.Integer, 
        db.ForeignKey('sfrs_component_database.experimental_chambers.id'), 
        nullable=True
    )

    # Disambiguated relationship
    experimental_chamber = db.relationship(
        'ExperimentalChamber',
        back_populates='musics',
        foreign_keys=[experimental_chamber_id]   
    )
    __mapper_args__ = {
        'polymorphic_identity': 'music'
    }

# Derived class for Quadrupole
class Quadrupole(Element):
    __tablename__ = 'quadrupoles'
    __table_args__ = {'schema': 'sfrs_component_database'}  

    id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.elements.id'),
        primary_key=True
    )

    multiplett_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.multipletts.id'),
        nullable=True
    )

    multiplett = db.relationship(
        'Multiplett',
        back_populates='quadrupoles',
        foreign_keys=[multiplett_id]
    )
    loc = db.Column(db.JSON, nullable=True)
    is_superconducting = db.Column(db.Boolean, nullable = True)
    is_horizontal_focusing = db.Column(db.Boolean, nullable=True)
    position_in_multiplett = db.Column(db.Integer, nullable = True)
    magnetic_measurements = db.Column(db.PickleType, nullable=True)
    GDL_max = db.Column(db.Float, nullable=True)
    nominal_current = db.Column(db.Float, nullable=True)
    __mapper_args__ = {
        'polymorphic_identity': 'quadrupole'
    }

# Derived class for Sextupoles
class Sextupole(Element):
    __tablename__ = 'sextupoles'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    multiplett_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.multipletts.id'),
        nullable=True
    )

    multiplett = db.relationship(
        'Multiplett',
        back_populates='sextupoles',
        foreign_keys=[multiplett_id]
    )
    loc = db.Column(db.JSON, nullable=True)
    is_superconducting = db.Column(db.Boolean, nullable = True)
    position_in_multiplett = db.Column(db.Integer, nullable = True)
    magnetic_measurements = db.Column(db.PickleType, nullable=True)
    SDL_max = db.Column(db.Float, nullable=True)
    nominal_current = db.Column(db.Float, nullable=True)
    __mapper_args__ = {
        'polymorphic_identity': 'sextupole'
    }

# Derived class for Octupole
class Octupole(Element):
    __tablename__ = 'octupoles'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    multiplett_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.multipletts.id'),
        nullable=True
    )

    multiplett = db.relationship(
        'Multiplett',
        back_populates='octupoles',
        foreign_keys=[multiplett_id]
    )
    loc = db.Column(db.JSON, nullable=True)
    is_superconducting = db.Column(db.Boolean, nullable = True)
    position_in_multiplett = db.Column(db.Integer, nullable = True)
    magnetic_measurements = db.Column(db.PickleType, nullable=True)
    ODL_max = db.Column(db.Float, nullable=True)
    nominal_current = db.Column(db.Float, nullable=True)
    __mapper_args__ = {
        'polymorphic_identity': 'octupole'
    }

# Derived class for Steerer
class Steerer(Element):
    __tablename__ = 'steerer'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    multiplett_id = db.Column(
        db.Integer,
        db.ForeignKey('sfrs_component_database.multipletts.id'),
        nullable=True
    )

    multiplett = db.relationship(
        'Multiplett',
        back_populates='steerer',
        foreign_keys=[multiplett_id]
    )
    loc = db.Column(db.JSON, nullable=True)
    is_superconducting = db.Column(db.Boolean, nullable = True)
    is_vertical_bending = db.Column(db.Boolean, nullable=True)
    position_in_multiplett = db.Column(db.Integer, nullable = True)
    magnetic_measurements = db.Column(db.PickleType, nullable=True)
    BDL_max = db.Column(db.Float, nullable=True)
    nominal_current = db.Column(db.Float, nullable=True)
    __mapper_args__ = {
        'polymorphic_identity': 'steerer'
    }

class Drift(Element):
    __tablename__ = 'beamlines'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    loc = db.Column(db.JSON, nullable=True)
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    __mapper_args__ = {
        'polymorphic_identity': 'drift'
    }

class FocalPlane(Element):
    __tablename__ = 'focal_plane'
    __table_args__ = {'schema': 'sfrs_component_database'} 
    loc = db.Column(db.JSON, nullable=True)
    id = db.Column(db.Integer, db.ForeignKey('sfrs_component_database.elements.id'), primary_key=True)
    __mapper_args__ = {
        'polymorphic_identity': 'focal_plane'
    }

