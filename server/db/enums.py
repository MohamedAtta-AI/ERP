from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    WORKER = "worker"


class PersonStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    ON_LEAVE = "on_leave"


class PayCycle(str, Enum):
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    DAILY = "daily"


class WorkerType(str, Enum):
    PERMANENT = "permanent"
    TEMP = "temp"
    CONTRACTOR = "contractor"


class DocType(str, Enum):
    NATIONAL_ID = "national_id"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    VISA = "visa"
    OTHER = "other"


class PaymentMethod(str, Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    WALLET = "wallet"
    INSTAPAY = "instapay"


class WalletProvider(str, Enum):
    VODAFONE_CASH = "Vodafone Cash"
    ETSALAT_CASH = "Etsalat Cash"
    ORANGE_CASH = "Orange Cash"
    WE_PAY = "WE Pay"
    INSTAPAY = "Instapay"


class CalculationMethod(str, Enum):
    FIXED = "fixed"
    PER_DAY = "per_day"
    PER_HOUR = "per_hour"
    PER_MONTH = "per_month"
    PER_YEAR = "per_year"
    PERCENTAGE = "percentage"


class ComponentCategory(str, Enum):
    EARNING = "earning"
    DEDUCTION = "deduction"


class ComponentType(str, Enum):
    # Earnings
    BASIC = "basic"
    OVERTIME = "overtime"
    ALLOWANCE = "allowance"
    INCENTIVE = "incentive"

    # Deductions
    TAX = "tax"
    INSURANCE = "insurance"
    PENALTY = "penalty"

    OTHER = "other"


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    OVERTIME_PENDING = "overtime_pending"
    OVERTIME_REJECTED = "overtime_rejected"
    OVERTIME_APPROVED = "overtime_approved"
