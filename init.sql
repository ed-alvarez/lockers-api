--
-- PostgreSQL database dump
--

-- Dumped from database version 15.1
-- Dumped by pg_dump version 15.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: billingperiod; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.billingperiod AS ENUM (
    'day',
    'week',
    'month',
    'year'
);


ALTER TYPE public.billingperiod OWNER TO koloni;

--
-- Name: billingtype; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.billingtype AS ENUM (
    'one_time',
    'recurring'
);


ALTER TYPE public.billingtype OWNER TO koloni;

--
-- Name: currency; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.currency AS ENUM (
    'usd',
    'eur',
    'gbp',
    'aud',
    'cad'
);


ALTER TYPE public.currency OWNER TO koloni;

--
-- Name: discounttype; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.discounttype AS ENUM (
    'percentage',
    'fixed'
);


ALTER TYPE public.discounttype OWNER TO koloni;

--
-- Name: eventstatus; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.eventstatus AS ENUM (
    'in_progress',
    'awaiting_payment_confirmation',
    'awaiting_service_pickup',
    'awaiting_service_dropoff',
    'awaiting_user_pickup',
    'transaction_in_progress',
    'finished',
    'canceled',
    'refunded',
    'reserved',
    'expired'
);


ALTER TYPE public.eventstatus OWNER TO koloni;

--
-- Name: eventtype; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.eventtype AS ENUM (
    'service',
    'rental',
    'storage',
    'delivery',
    'vending'
);


ALTER TYPE public.eventtype OWNER TO koloni;

--
-- Name: expirationunit; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.expirationunit AS ENUM (
    'hours',
    'days'
);


ALTER TYPE public.expirationunit OWNER TO koloni;

--
-- Name: hardwaretype; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.hardwaretype AS ENUM (
    'linka',
    'spintly',
    'ojmar',
    'keynius',
    'gantner',
    'harbor',
    'dclock',
    'virtual'
);


ALTER TYPE public.hardwaretype OWNER TO koloni;

--
-- Name: issuestatus; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.issuestatus AS ENUM (
    'pending',
    'in_progress',
    'resolved'
);


ALTER TYPE public.issuestatus OWNER TO koloni;

--
-- Name: lockstatus; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.lockstatus AS ENUM (
    'open',
    'locked',
    'unknown',
    'offline',
    'closed'
);


ALTER TYPE public.lockstatus OWNER TO koloni;

--
-- Name: logtype; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.logtype AS ENUM (
    'lock',
    'unlock',
    'maintenance',
    'report_issue'
);


ALTER TYPE public.logtype OWNER TO koloni;

--
-- Name: membershiptype; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.membershiptype AS ENUM (
    'unlimited',
    'limited',
    'percentage',
    'fixed'
);


ALTER TYPE public.membershiptype OWNER TO koloni;

--
-- Name: mode; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.mode AS ENUM (
    'service',
    'storage',
    'rental',
    'delivery',
    'vending'
);


ALTER TYPE public.mode OWNER TO koloni;

--
-- Name: notificationtype; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.notificationtype AS ENUM (
    'on_signup',
    'on_start',
    'in_progress',
    'on_complete',
    'on_service_pickup',
    'on_service_charge',
    'on_service_dropoff',
    'on_reservation',
    'instructions',
    'marketing',
    'reminder',
    'custom',
    'non_locker_delivery',
    'on_expired'
);


ALTER TYPE public.notificationtype OWNER TO koloni;

--
-- Name: penalizereason; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.penalizereason AS ENUM (
    'missing_items',
    'damaged_items',
    'misconduct',
    'other'
);


ALTER TYPE public.penalizereason OWNER TO koloni;

--
-- Name: pricetype; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.pricetype AS ENUM (
    'pay_per_weight',
    'pay_per_time'
);


ALTER TYPE public.pricetype OWNER TO koloni;

--
-- Name: productcondition; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.productcondition AS ENUM (
    'new',
    'good',
    'usable',
    'broken'
);


ALTER TYPE public.productcondition OWNER TO koloni;

--
-- Name: recipienttype; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.recipienttype AS ENUM (
    'user',
    'admin'
);


ALTER TYPE public.recipienttype OWNER TO koloni;

--
-- Name: restimeunit; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.restimeunit AS ENUM (
    'minute',
    'hour',
    'day',
    'week'
);


ALTER TYPE public.restimeunit OWNER TO koloni;

--
-- Name: roletype; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.roletype AS ENUM (
    'admin',
    'member',
    'viewer',
    'operator'
);


ALTER TYPE public.roletype OWNER TO koloni;

--
-- Name: signinmethod; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.signinmethod AS ENUM (
    'email',
    'phone',
    'both'
);


ALTER TYPE public.signinmethod OWNER TO koloni;

--
-- Name: state; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.state AS ENUM (
    'new',
    'incoming',
    'outgoing',
    'maintenance'
);


ALTER TYPE public.state OWNER TO koloni;

--
-- Name: status; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.status AS ENUM (
    'available',
    'reserved',
    'maintenance',
    'expired'
);


ALTER TYPE public.status OWNER TO koloni;

--
-- Name: stripecountry; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.stripecountry AS ENUM (
    'AT',
    'BE',
    'FI',
    'FR',
    'DE',
    'IE',
    'IT',
    'NL',
    'PT',
    'ES',
    'GB',
    'AU',
    'CA',
    'US'
);


ALTER TYPE public.stripecountry OWNER TO koloni;

--
-- Name: timeunit; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.timeunit AS ENUM (
    'minute',
    'hour',
    'day',
    'week',
    'immediately'
);


ALTER TYPE public.timeunit OWNER TO koloni;

--
-- Name: unit; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.unit AS ENUM (
    'minute',
    'hour',
    'day',
    'week',
    'lb',
    'kg'
);


ALTER TYPE public.unit OWNER TO koloni;

--
-- Name: webhookstatus; Type: TYPE; Schema: public; Owner: koloni
--

CREATE TYPE public.webhookstatus AS ENUM (
    'ok',
    'error',
    'inactive'
);


ALTER TYPE public.webhookstatus OWNER TO koloni;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: User; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public."User" (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    name character varying DEFAULT 'User'::character varying NOT NULL,
    active boolean DEFAULT true NOT NULL,
    phone_number character varying,
    email character varying,
    user_id character varying,
    pin_code character varying,
    address character varying,
    require_auth boolean NOT NULL,
    access_code character(6)
);


ALTER TABLE public."User" OWNER TO koloni;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO koloni;

--
-- Name: api_key; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.api_key (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    key character varying NOT NULL,
    active boolean NOT NULL,
    id_org uuid NOT NULL
);


ALTER TABLE public.api_key OWNER TO koloni;

--
-- Name: apscheduler_jobs; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.apscheduler_jobs (
    id character varying(191) NOT NULL,
    next_run_time double precision,
    job_state bytea NOT NULL
);


ALTER TABLE public.apscheduler_jobs OWNER TO koloni;

--
-- Name: codes; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.codes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    code character varying NOT NULL,
    id_user uuid NOT NULL,
    id_org uuid NOT NULL
);


ALTER TABLE public.codes OWNER TO koloni;

--
-- Name: cognito_members_role_link; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.cognito_members_role_link (
    user_id uuid NOT NULL,
    role_id uuid NOT NULL
);


ALTER TABLE public.cognito_members_role_link OWNER TO koloni;

--
-- Name: condition; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.condition (
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    id uuid NOT NULL,
    name character varying NOT NULL,
    auto_report boolean NOT NULL,
    auto_maintenance boolean NOT NULL,
    id_org uuid NOT NULL
);


ALTER TABLE public.condition OWNER TO koloni;

--
-- Name: device; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.device (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    name character varying NOT NULL,
    custom_identifier character varying,
    item character varying,
    item_description character varying,
    image character varying,
    locker_number integer,
    mode public.mode NOT NULL,
    status public.status NOT NULL,
    hardware_type public.hardwaretype NOT NULL,
    lock_status public.lockstatus NOT NULL,
    price_required boolean NOT NULL,
    transaction_count integer NOT NULL,
    mac_address character varying,
    integration_id integer,
    locker_udn character varying,
    user_code character varying,
    master_code character varying,
    gantner_id character varying,
    keynius_id character varying,
    harbor_tower_id character varying,
    harbor_locker_id character varying,
    dclock_terminal_no character varying,
    dclock_box_no character varying,
    id_location uuid,
    id_size uuid,
    id_price uuid,
    id_product uuid,
    id_condition uuid,
    id_locker_wall uuid,
    id_org uuid NOT NULL,
    shared boolean DEFAULT false NOT NULL,
    require_image boolean DEFAULT false NOT NULL
);


ALTER TABLE public.device OWNER TO koloni;

--
-- Name: event; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.event (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at timestamp with time zone,
    ended_at timestamp with time zone,
    invoice_id character varying,
    order_id character varying,
    payment_intent_id character varying,
    setup_intent_id character varying,
    stripe_subscription_id character varying,
    harbor_session_seed character varying,
    harbor_session_token character varying,
    harbor_session_token_auth character varying,
    harbor_payload character varying,
    harbor_payload_auth character varying,
    harbor_reservation_id character varying,
    code bigint,
    passcode character varying,
    event_status public.eventstatus NOT NULL,
    event_type public.eventtype NOT NULL,
    total numeric(8,2),
    total_time character varying,
    refunded_amount numeric(8,2) NOT NULL,
    signature_url character varying,
    id_org uuid NOT NULL,
    id_user uuid,
    id_device uuid NOT NULL,
    image_url character varying,
    courier_pin_code character varying,
    id_promo uuid,
    penalize_charge numeric(6,2),
    penalize_reason public.penalizereason,
    weight numeric(6,2),
    canceled_at timestamp with time zone,
    canceled_by character varying,
    id_membership uuid
);


ALTER TABLE public.event OWNER TO koloni;

--
-- Name: feedback; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.feedback (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    id_org uuid NOT NULL,
    id_location uuid,
    id_device uuid,
    member character varying,
    department character varying,
    image character varying,
    description character varying NOT NULL,
    notes character varying NOT NULL
);


ALTER TABLE public.feedback OWNER TO koloni;

--
-- Name: groups; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.groups (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    name character varying NOT NULL,
    id_org uuid NOT NULL
);


ALTER TABLE public.groups OWNER TO koloni;

--
-- Name: harbor_events; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.harbor_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tower_id character varying NOT NULL,
    locker_id character varying NOT NULL,
    pin_code character varying,
    status character varying NOT NULL
);


ALTER TABLE public.harbor_events OWNER TO koloni;

--
-- Name: issue; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.issue (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    pictures character varying[],
    issue_id character varying,
    description character varying NOT NULL,
    status public.issuestatus NOT NULL,
    id_org uuid NOT NULL,
    id_user uuid,
    id_event uuid,
    team_member_id uuid
);


ALTER TABLE public.issue OWNER TO koloni;

--
-- Name: link_device_price; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.link_device_price (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    id_device uuid NOT NULL,
    id_price uuid NOT NULL
);


ALTER TABLE public.link_device_price OWNER TO koloni;

--
-- Name: link_groups_devices; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.link_groups_devices (
    id uuid NOT NULL,
    id_group uuid NOT NULL,
    id_device uuid NOT NULL
);


ALTER TABLE public.link_groups_devices OWNER TO koloni;

--
-- Name: link_groups_locations; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.link_groups_locations (
    id uuid NOT NULL,
    id_group uuid NOT NULL,
    id_location uuid NOT NULL
);


ALTER TABLE public.link_groups_locations OWNER TO koloni;

--
-- Name: link_groups_user; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.link_groups_user (
    id uuid NOT NULL,
    id_group uuid NOT NULL,
    id_user uuid NOT NULL
);


ALTER TABLE public.link_groups_user OWNER TO koloni;

--
-- Name: link_member_location; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.link_member_location (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id character varying NOT NULL,
    id_location uuid NOT NULL
);


ALTER TABLE public.link_member_location OWNER TO koloni;

--
-- Name: link_membership_location; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.link_membership_location (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    id_membership uuid NOT NULL,
    id_location uuid NOT NULL
);


ALTER TABLE public.link_membership_location OWNER TO koloni;

--
-- Name: link_notification_location; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.link_notification_location (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    id_notification uuid NOT NULL,
    id_location uuid NOT NULL
);


ALTER TABLE public.link_notification_location OWNER TO koloni;

--
-- Name: link_org_user; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.link_org_user (
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    id_org uuid NOT NULL,
    id_user uuid NOT NULL,
    id_membership uuid,
    id_favorite_location uuid,
    stripe_customer_id character varying,
    stripe_subscription_id character varying
);


ALTER TABLE public.link_org_user OWNER TO koloni;

--
-- Name: link_user_devices; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.link_user_devices (
    id uuid NOT NULL,
    id_user uuid NOT NULL,
    id_device uuid NOT NULL
);


ALTER TABLE public.link_user_devices OWNER TO koloni;

--
-- Name: link_user_locations; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.link_user_locations (
    id uuid NOT NULL,
    id_user uuid NOT NULL,
    id_location uuid NOT NULL
);


ALTER TABLE public.link_user_locations OWNER TO koloni;

--
-- Name: lite_app_settings; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.lite_app_settings (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    id_org uuid NOT NULL,
    sign_in_method public.signinmethod,
    allow_multiple_rentals boolean,
    allow_user_reservation boolean,
    track_product_condition boolean,
    allow_photo_end_rental boolean,
    setup_in_app_payment boolean,
    primary_color character varying,
    secondary_color character varying
);


ALTER TABLE public.lite_app_settings OWNER TO koloni;

--
-- Name: location; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.location (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    hidden boolean,
    contact_email character varying,
    contact_phone character varying,
    name character varying NOT NULL,
    custom_id character varying,
    address character varying NOT NULL,
    image character varying,
    latitude numeric(18,15) NOT NULL,
    longitude numeric(18,15) NOT NULL,
    restrict_by_user_code boolean NOT NULL,
    verify_pin_code boolean NOT NULL,
    verify_qr_code boolean NOT NULL,
    verify_url boolean NOT NULL,
    verify_signature boolean NOT NULL,
    email boolean NOT NULL,
    phone boolean NOT NULL,
    id_org uuid NOT NULL,
    id_price uuid,
    shared boolean DEFAULT false NOT NULL
);


ALTER TABLE public.location OWNER TO koloni;

--
-- Name: locker_wall; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.locker_wall (
    lockers json NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    image character varying,
    name character varying NOT NULL,
    description character varying,
    custom_id character varying,
    qty_wide integer NOT NULL,
    qty_tall integer NOT NULL,
    is_kiosk boolean NOT NULL,
    id_org uuid NOT NULL,
    id_location uuid
);


ALTER TABLE public.locker_wall OWNER TO koloni;

--
-- Name: log; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.log (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    id_org uuid NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    id_event uuid,
    id_device uuid NOT NULL,
    log_owner character varying,
    log_type public.logtype NOT NULL
);


ALTER TABLE public.log OWNER TO koloni;

--
-- Name: memberships; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.memberships (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at timestamp without time zone,
    name character varying NOT NULL,
    description character varying NOT NULL,
    active boolean NOT NULL,
    currency public.currency NOT NULL,
    amount numeric(18,2) NOT NULL,
    billing_type public.billingtype NOT NULL,
    billing_period public.billingperiod NOT NULL,
    number_of_payments integer NOT NULL,
    membership_type public.membershiptype NOT NULL,
    value double precision NOT NULL,
    stripe_product_id character varying NOT NULL,
    stripe_price_id character varying NOT NULL,
    id_org uuid NOT NULL
);


ALTER TABLE public.memberships OWNER TO koloni;

--
-- Name: notification; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.notification (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    name character varying NOT NULL,
    message character varying NOT NULL,
    mode public.eventtype NOT NULL,
    notification_type public.notificationtype NOT NULL,
    event public.eventstatus,
    time_amount numeric(8,2) NOT NULL,
    time_unit public.timeunit NOT NULL,
    before boolean NOT NULL,
    after boolean NOT NULL,
    email boolean NOT NULL,
    sms boolean NOT NULL,
    push boolean NOT NULL,
    email_2nd boolean NOT NULL,
    sms_2nd boolean NOT NULL,
    push_2nd boolean NOT NULL,
    is_template boolean NOT NULL,
    id_org uuid NOT NULL,
    id_member uuid,
    recipient_type public.recipienttype DEFAULT 'user'::public.recipienttype NOT NULL
);


ALTER TABLE public.notification OWNER TO koloni;

--
-- Name: org; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.org (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying NOT NULL,
    active boolean,
    user_pool character varying,
    client_id character varying,
    stripe_account_id character varying,
    twilio_sid character varying,
    rental_mode boolean NOT NULL,
    storage_mode boolean NOT NULL,
    delivery_mode boolean NOT NULL,
    service_mode boolean NOT NULL,
    super_tenant boolean NOT NULL,
    id_tenant uuid,
    linka_hardware boolean DEFAULT true NOT NULL,
    ojmar_hardware boolean DEFAULT true NOT NULL,
    gantner_hardware boolean DEFAULT true NOT NULL,
    harbor_hardware boolean DEFAULT true NOT NULL,
    dclock_hardware boolean DEFAULT true NOT NULL,
    spintly_hardware boolean DEFAULT true NOT NULL,
    lite_app_enabled boolean DEFAULT true NOT NULL,
    pending_delete boolean DEFAULT false NOT NULL,
    delete_issuer uuid,
    pricing boolean DEFAULT true NOT NULL,
    product boolean DEFAULT true NOT NULL,
    notifications boolean DEFAULT true NOT NULL,
    multi_tenant boolean DEFAULT true NOT NULL,
    toolbox boolean DEFAULT true NOT NULL,
    vending_mode boolean DEFAULT true NOT NULL
);


ALTER TABLE public.org OWNER TO koloni;

--
-- Name: org_filters; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.org_filters (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    id_org uuid NOT NULL,
    pay_per character varying NOT NULL,
    subscriptions character varying NOT NULL,
    promo_codes character varying NOT NULL,
    locations character varying NOT NULL,
    devices character varying NOT NULL,
    sizes character varying NOT NULL,
    transactions character varying DEFAULT '[{"label": "Select", "value": "select", "active": true}, {"label": "Invoice ID", "value": "invoice_id", "active": true, "sortable": true}, {"label": "Order Number", "value": "order_id", "active": true, "sortable": true}, {"label": "User Phone", "value": "user_phone", "active": true, "sortable": true}, {"label": "User Email", "value": "user_email", "active": true, "sortable": true}, {"label": "Device Name", "value": "device_name", "active": true, "sortable": true}, {"label": "Locker Number", "value": "locker_number", "active": true, "sortable": true}, {"label": "Location", "value": "location", "active": true, "sortable": true}, {"label": "Mode", "value": "mode", "active": true, "sortable": true}, {"label": "Status", "value": "status", "active": true, "sortable": true}, {"label": "Start Date", "value": "start_date", "active": true, "sortable": true}, {"label": "End Date", "value": "end_date", "active": true, "sortable": true}, {"label": "Duration", "value": "duration", "active": true}, {"label": "Refund", "value": "refund", "active": true, "sortable": true}, {"label": "Amount", "value": "amount", "active": true}, {"label": "End", "value": "end", "active": true}, {"label": "QR Code", "value": "qr_code", "active": true}, {"label": "Action", "value": "action", "active": true}]'::jsonb NOT NULL,
    users character varying NOT NULL,
    members character varying NOT NULL,
    groups character varying NOT NULL,
    issues character varying NOT NULL,
    notifications character varying NOT NULL,
    inventory character varying NOT NULL,
    product_groups character varying NOT NULL,
    conditions character varying NOT NULL,
    reservations character varying DEFAULT '[{"label": "Select", "value": "select", "active": true}, {"label": "Mode", "value": "mode", "active": true}, {"label": "Tracking Number", "value": "tracking_number", "active": true}, {"label": "User", "value": "user", "active": true, "sortable": true}, {"label": "Phone Number", "value": "phone", "active": true, "sortable": true}, {"label": "Email", "value": "email", "active": true, "sortable": true}, {"label": "Duration", "value": "duration", "active": true}, {"label": "Date", "value": "date", "active": true, "sortable": true}, {"label": "Assigned Locker", "value": "assigned_locker", "active": true, "sortable": true}, {"label": "Location", "value": "location", "active": true, "sortable": true}, {"label": "Size", "value": "size", "active": true, "sortable": true}, {"label": "Action", "value": "action", "active": true}]'::jsonb NOT NULL,
    reporting text DEFAULT '[{"label": "Select", "value": "select", "active": true}, {"label": "Report Name", "value": "report_name", "active": true, "sortable": true}, {"label": "Contents", "value": "contents", "active": true, "sortable": true}, {"label": "Asignee", "value": "asignee", "active": true, "sortable": true}, {"label": "Send Date", "value": "send_date", "active": true, "sortable": true}, {"label": "Previous", "value": "previous", "active": true}, {"label": "Action", "value": "action", "active": true}]'::jsonb,
    subscribers character varying DEFAULT '[{"label": "User Name", "value": "name", "active": true, "sortable": true}, {"label": "Price", "value": "price", "active": true, "sortable": true}, {"label": "Expiry", "value": "expiration_date", "active": true, "sortable": true}, {"label": "Recurring", "value": "recurring", "active": true, "sortable": true}, {"label": "Membership Name", "value": "membership_name", "active": true, "sortable": true}, {"label": "No. of transactions left", "value": "no_of_transactions", "active": true, "sortable": true}]'::jsonb
);


ALTER TABLE public.org_filters OWNER TO koloni;

--
-- Name: org_settings; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.org_settings (
    id uuid NOT NULL,
    id_org uuid NOT NULL,
    default_country public.stripecountry,
    default_max_reservations integer,
    default_time_zone character varying,
    default_date_format character varying,
    delivery_sms_start character varying,
    service_sms_start character varying,
    service_sms_charge character varying,
    service_sms_end character varying,
    event_sms_refund character varying,
    invoice_prefix character varying,
    default_device_hardware public.hardwaretype,
    default_device_mode public.mode,
    default_id_price uuid,
    default_support_email character varying,
    default_support_phone character varying,
    language character(2) DEFAULT 'en'::bpchar NOT NULL,
    default_currency public.currency DEFAULT 'usd'::public.currency NOT NULL,
    default_id_size uuid,
    maintenance_on_issue boolean DEFAULT true NOT NULL,
    parcel_expiration integer,
    parcel_expiration_unit public.expirationunit,
    use_long_parcel_codes boolean
);


ALTER TABLE public.org_settings OWNER TO koloni;

--
-- Name: price; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.price (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    name character varying NOT NULL,
    amount numeric(8,2) NOT NULL,
    currency public.currency NOT NULL,
    prorated boolean NOT NULL,
    card_on_file boolean NOT NULL,
    unit public.unit NOT NULL,
    unit_amount numeric(8,2) NOT NULL,
    price_type public.pricetype NOT NULL,
    id_org uuid NOT NULL,
    "default" boolean DEFAULT false NOT NULL
);


ALTER TABLE public.price OWNER TO koloni;

--
-- Name: product; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.product (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    image character varying,
    name character varying NOT NULL,
    description character varying,
    price numeric(8,2),
    sales_price numeric(8,2),
    sku character varying,
    msrp character varying,
    serial_number character varying,
    id_condition uuid,
    condition public.productcondition NOT NULL,
    repair_on_broken boolean NOT NULL,
    report_on_broken boolean NOT NULL,
    id_org uuid NOT NULL,
    id_product_group uuid
);


ALTER TABLE public.product OWNER TO koloni;

--
-- Name: product_group; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.product_group (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    name character varying NOT NULL,
    charging_time integer NOT NULL,
    one_to_one boolean NOT NULL,
    id_org uuid NOT NULL,
    id_size uuid,
    total_inventory integer NOT NULL,
    transaction_number integer DEFAULT 0 NOT NULL,
    auto_repair boolean DEFAULT false NOT NULL
);


ALTER TABLE public.product_group OWNER TO koloni;

--
-- Name: product_tracking; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.product_tracking (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    state public.state NOT NULL,
    id_org uuid NOT NULL,
    id_product uuid NOT NULL,
    id_user uuid,
    id_device uuid,
    id_condition uuid
);


ALTER TABLE public.product_tracking OWNER TO koloni;

--
-- Name: promo; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.promo (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    start_time timestamp with time zone,
    end_time timestamp with time zone,
    name character varying NOT NULL,
    code character varying NOT NULL,
    amount numeric(8,2) NOT NULL,
    discount_type public.discounttype NOT NULL,
    id_org uuid NOT NULL
);


ALTER TABLE public.promo OWNER TO koloni;

--
-- Name: report; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.report (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    name character varying NOT NULL,
    contents character varying[] NOT NULL,
    id_org uuid NOT NULL,
    version character varying,
    target_org uuid,
    assign_to uuid[] DEFAULT ARRAY[]::uuid[] NOT NULL,
    send_time character varying DEFAULT '00:00'::character varying NOT NULL,
    last_content character varying[],
    last_sent timestamp with time zone,
    recurrence character varying,
    weekday integer,
    month integer
);


ALTER TABLE public.report OWNER TO koloni;

--
-- Name: reservation; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.reservation (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    start_date timestamp with time zone,
    end_date timestamp with time zone,
    recurring boolean,
    sunday boolean,
    monday boolean,
    tuesday boolean,
    wednesday boolean,
    thursday boolean,
    friday boolean,
    saturday boolean,
    from_time character varying,
    to_time character varying,
    id_org uuid NOT NULL,
    id_user uuid,
    id_device uuid,
    id_location uuid,
    id_size uuid,
    id_product uuid,
    mode public.mode,
    tracking_number character varying
);


ALTER TABLE public.reservation OWNER TO koloni;

--
-- Name: reservation_settings; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.reservation_settings (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    id_org uuid NOT NULL,
    max_rental_time integer DEFAULT 0 NOT NULL,
    max_rental_time_period public.restimeunit DEFAULT 'hour'::public.restimeunit NOT NULL,
    max_reservation_time integer DEFAULT 0 NOT NULL,
    max_reservation_time_period public.restimeunit DEFAULT 'hour'::public.restimeunit NOT NULL,
    transaction_buffer_time integer DEFAULT 0 NOT NULL,
    locker_buffer_time integer DEFAULT 0 NOT NULL,
    transaction_buffer_time_period public.restimeunit,
    locker_buffer_time_period public.restimeunit
);


ALTER TABLE public.reservation_settings OWNER TO koloni;

--
-- Name: reservation_widget_settings; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.reservation_widget_settings (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    id_org uuid NOT NULL,
    primary_color character varying,
    secondary_color character varying,
    background_color character varying,
    duration integer,
    in_app_payment boolean,
    duration_unit public.restimeunit DEFAULT 'hour'::public.restimeunit NOT NULL
);


ALTER TABLE public.reservation_widget_settings OWNER TO koloni;

--
-- Name: role; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.role (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    role public.roletype NOT NULL,
    user_id character varying NOT NULL,
    id_org uuid NOT NULL,
    pin_code character varying
);


ALTER TABLE public.role OWNER TO koloni;

--
-- Name: role_permission; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.role_permission (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    role_id uuid NOT NULL,
    permission character varying NOT NULL
);


ALTER TABLE public.role_permission OWNER TO koloni;

--
-- Name: size; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.size (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    name character varying NOT NULL,
    external_id character varying,
    width numeric(8,4) NOT NULL,
    depth numeric(8,4) NOT NULL,
    height numeric(8,4) NOT NULL,
    id_org uuid NOT NULL,
    image character varying DEFAULT 'https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/fceab2de675e4f87a2187e26e1f3bfa5.png'::character varying,
    description text
);


ALTER TABLE public.size OWNER TO koloni;

--
-- Name: webhook; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.webhook (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    url character varying NOT NULL,
    signature_key character varying NOT NULL,
    status public.webhookstatus NOT NULL,
    id_org uuid NOT NULL
);


ALTER TABLE public.webhook OWNER TO koloni;

--
-- Name: white_label; Type: TABLE; Schema: public; Owner: koloni
--

CREATE TABLE public.white_label (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    image_key character varying,
    app_logo character varying,
    app_name character varying NOT NULL,
    primary_color character varying NOT NULL,
    secondary_color character varying NOT NULL,
    tertiary_color character varying,
    link_text_color character varying NOT NULL,
    button_text_color character varying NOT NULL,
    privacy_policy character varying NOT NULL,
    user_agreement character varying NOT NULL,
    terms_condition character varying NOT NULL,
    organization_owner character varying,
    id_org uuid NOT NULL,
    terms_condition_2nd character varying,
    terms_name_2nd character varying
);


ALTER TABLE public.white_label OWNER TO koloni;

--
-- Data for Name: User; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public."User" (id, created_at, name, active, phone_number, email, user_id, pin_code, address, require_auth, access_code) FROM stdin;
0c508cf5-797a-46f4-b379-5fb23268c789	2023-09-28 16:13:28.005211+00	User	t	+1223334444	\N	\N	\N	\N	f	\N
796efd9e-cfd0-4347-b25e-30de3099f2ea	2023-09-28 21:03:10.84+00	Timmy	t	+1234567890	timmy@koloni.me	\N	\N	\N	f	\N
ab292219-76e8-47a7-8dc8-778778613a84	2023-06-29 17:47:49.26606+00	Eduardo Alvarez	t	+50683717112	ed.alv.mart@koloni.me	string	\N	string	f	\N
28a64e1b-2114-433f-899d-14cf6f52d243	2023-09-28 17:52:19.96925+00	John Doe	t	+50684757437	dev.victor.warren@gmail.com	\N	\N	string	f	\N
bf02b6d9-fad2-4c7a-ba34-b60efe735f9d	2023-11-29 18:34:55.995223+00	string	t	\N	test@email.com	24443	5382	string	t	\N
617801bb-d2fa-47c6-8628-a0c1c89f2fa1	2023-11-29 18:39:41.85053+00	Test	t	\N	test23@email.com	78787878	7041	test	t	\N
2336e1f5-471b-4267-827b-5a9a9847a928	2023-01-18 00:42:36.90055+00	User	t	\N	julio@koloni.me	\N	3041	\N	t	\N
c90308b9-24db-4f17-b397-d9a477f0031d	2023-12-08 18:16:08.894429+00	User	t	+50683350526	\N	\N	\N	\N	f	\N
9b836bd4-ec75-446b-a96a-b2f8957ae98a	2023-05-12 16:16:57.164585+00	Eduardo Alvarez	t	+50683717118	eduardo@koloni.me	5	\N	\N	f	\N
e8442381-7053-411c-9c43-1458ca7b18a2	2024-01-18 14:19:54.380492+00	User	t	+50683350526	\N	\N	\N	\N	f	\N
2c006625-1907-414d-8aca-60445d38835f	2023-10-24 18:19:09.71222+00	User	t	+50683717117	\N	\N	\N	\N	f	483521
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.alembic_version (version_num) FROM stdin;
c07a10757132
\.


--
-- Data for Name: api_key; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.api_key (id, created_at, key, active, id_org) FROM stdin;
5be5a0ff-63e2-4d2b-a3cc-0e3633283c8e	2023-05-04 18:04:13.799002+00	YmNiMTM2OWIzOWE5OTMxOWYyOGVlNzI4MDgxY2Q4MGEwYWFmMjljNTYwODA5MGFjNTM1MDU3MTcwMzk2Y2I3ZQ	t	fec27db7-466a-48a1-956b-cbfd7c9eb9d9
9cc3a54e-8280-43d3-82fa-7e313881b812	2023-05-10 18:54:31.369059+00	MmU2NWMyMGM0NzJkMjg0NzA3MWFlYjZkZjAwZTA0OWVmODAwMzY2NGQ2ZWY0ODhhNjNmMzJkM2Y3Y2NlNTQyZA	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a
\.


--
-- Data for Name: apscheduler_jobs; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.apscheduler_jobs (id, next_run_time, job_state) FROM stdin;
\.


--
-- Data for Name: codes; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.codes (id, code, id_user, id_org) FROM stdin;
\.


--
-- Data for Name: cognito_members_role_link; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.cognito_members_role_link (user_id, role_id) FROM stdin;
\.


--
-- Data for Name: condition; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.condition (created_at, id, name, auto_report, auto_maintenance, id_org) FROM stdin;
2023-11-22 17:57:01.495103+00	ba1b1256-b055-4c16-803c-993169a3c8b6	string	t	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a
2023-12-07 14:58:38.418923+00	2fb7551c-b590-47b0-87f5-a8357f1b6f18	Test	f	f	bc6647fb-90d8-4c79-87e9-9b6942383e4a
\.


--
-- Data for Name: device; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.device (id, created_at, name, custom_identifier, item, item_description, image, locker_number, mode, status, hardware_type, lock_status, price_required, transaction_count, mac_address, integration_id, locker_udn, user_code, master_code, gantner_id, keynius_id, harbor_tower_id, harbor_locker_id, dclock_terminal_no, dclock_box_no, id_location, id_size, id_price, id_product, id_condition, id_locker_wall, id_org, shared, require_image) FROM stdin;
0d295146-4e10-439e-a545-d4c93ee94c2b	2023-09-30 02:15:01.558906+00	storage_test_device	\N	\N	\N	\N	98	delivery	maintenance	linka	unknown	f	5	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2d573dc0-c92c-4007-82e4-28d8e7422686	feab97c9-b758-4be7-8b07-ebd6da8edfa7	\N	\N	\N	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	f	f
3b67256b-0869-4c6a-8720-391dd3d5b67d	2023-11-09 15:22:04.769053+00	Gantner Test Device	\N	\N	\N	\N	1337	rental	available	gantner	open	f	17	\N	\N	\N	\N	\N	01101689-2248070013-01	\N	\N	\N	\N	\N	880a7720-e92c-4395-a614-fbc61cbf5dfb	feab97c9-b758-4be7-8b07-ebd6da8edfa7	\N	\N	2fb7551c-b590-47b0-87f5-a8357f1b6f18	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	f	f
f83ef364-0b12-4c39-a8c9-27c10f1d32d7	2024-07-30 16:03:37.323996+00	Virtual Device Test	\N	\N	\N	\N	2553	storage	reserved	virtual	locked	f	2	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	5e27cb08-fdc8-44c7-9755-5853c3c2b5b1	69cfc633-59f7-4822-b706-b411ff17b04b	\N	\N	\N	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	f	f
7144fcf6-ce2b-47b8-afe3-58381c2449fc	2023-11-28 15:39:51.238226+00	RT	\N	\N	\N	\N	\N	vending	maintenance	virtual	locked	f	43	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	7c2b3a67-fc05-4b17-9c2f-2a23b7c9a7c7	1ff2cb0d-a79f-4559-bfd3-e90e5c2b1d68	\N	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	f	f
ec63afe1-098a-4170-9fde-27b72e2c6125	2023-10-04 17:50:31.123758+00	Test Device	\N	\N	\N	\N	\N	delivery	reserved	linka	unknown	f	6	AA:BB:CC:DD:EE:FF	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	24346412-25e3-408d-928a-d416d5fd034f	feab97c9-b758-4be7-8b07-ebd6da8edfa7	\N	\N	\N	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	f	f
\.


--
-- Data for Name: event; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.event (id, created_at, started_at, ended_at, invoice_id, order_id, payment_intent_id, setup_intent_id, stripe_subscription_id, harbor_session_seed, harbor_session_token, harbor_session_token_auth, harbor_payload, harbor_payload_auth, harbor_reservation_id, code, passcode, event_status, event_type, total, total_time, refunded_amount, signature_url, id_org, id_user, id_device, image_url, courier_pin_code, id_promo, penalize_charge, penalize_reason, weight, canceled_at, canceled_by, id_membership) FROM stdin;
af7ae6ac-a1f8-4d2c-b0af-1dc55e055ee6	2023-10-16 16:18:25.026974+00	2023-10-16 16:18:26.512653+00	2023-10-24 18:20:27.725218+00	TST000002	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	rental	\N	\N	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2c006625-1907-414d-8aca-60445d38835f	0d295146-4e10-439e-a545-d4c93ee94c2b	\N	\N	\N	\N	\N	\N	\N	\N	\N
1914f953-e6c7-4db1-ae4c-d20374261f7e	2023-10-24 18:19:53.358769+00	2023-10-24 18:19:54.9801+00	2023-10-24 18:21:34.324383+00	TST000003	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	finished	delivery	\N	\N	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2c006625-1907-414d-8aca-60445d38835f	0d295146-4e10-439e-a545-d4c93ee94c2b	\N	\N	\N	\N	\N	\N	\N	\N	\N
a91bf0ae-77ba-4b32-bb3e-01a304ce54a1	2023-10-24 18:40:07.239633+00	2023-10-24 18:40:08.726659+00	2023-11-08 15:49:21.550476+00	TST000005	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	finished	delivery	\N	357:09:12	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2c006625-1907-414d-8aca-60445d38835f	0d295146-4e10-439e-a545-d4c93ee94c2b	\N	\N	\N	\N	\N	\N	\N	\N	\N
6ecd572c-261b-4882-8b5e-351e671b70f6	2023-11-08 15:51:24.870391+00	2023-11-08 15:51:26.325617+00	2023-11-08 15:55:21.031168+00	TST000006	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	finished	delivery	\N	00:03:54	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2c006625-1907-414d-8aca-60445d38835f	0d295146-4e10-439e-a545-d4c93ee94c2b	\N	\N	\N	\N	\N	\N	\N	\N	\N
dc78143d-a222-43ad-be85-938c48f7e38a	2023-11-30 19:23:01.549491+00	2023-11-30 19:23:02.23553+00	2023-11-30 19:31:05.643246+00	TST000008	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	storage	\N	00:08:03	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2336e1f5-471b-4267-827b-5a9a9847a928	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
56e4d0a4-3de9-481d-a75d-60e7f5670ef9	2023-11-30 19:31:08.787154+00	2023-11-30 19:31:09.517176+00	2023-11-30 19:31:11.200655+00	TST000009	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	finished	storage	0.00	00:00:01	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2336e1f5-471b-4267-827b-5a9a9847a928	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
834f48b5-c8f7-4451-8db1-23878549de8a	2023-11-30 19:43:08.836975+00	2023-11-30 19:43:09.513305+00	2023-11-30 19:46:06.54086+00	TST000011	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	storage	\N	00:02:56	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2336e1f5-471b-4267-827b-5a9a9847a928	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
f00b9ed5-36cf-4ba8-bf76-8b174cc68c43	2023-11-30 19:35:08.847694+00	2023-11-30 19:35:09.537572+00	2023-11-30 19:46:20.025308+00	TST000010	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	storage	\N	00:11:10	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2336e1f5-471b-4267-827b-5a9a9847a928	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
45221b82-e7be-4528-8edd-f34d46bac79e	2023-11-30 19:50:08.737195+00	2023-11-30 19:50:08.739407+00	2023-11-30 19:56:08.737805+00	TST000012	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	storage	\N	00:05:59	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2336e1f5-471b-4267-827b-5a9a9847a928	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
61fff940-d408-4c6b-84d4-3a11450d8c05	2023-11-30 19:58:08.746551+00	2023-11-30 19:58:08.748885+00	2023-11-30 20:00:48.122345+00	TST000013	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	storage	\N	00:02:39	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2336e1f5-471b-4267-827b-5a9a9847a928	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
05cde206-8c10-46ad-a1df-3849707fef1d	2023-11-30 20:03:08.740732+00	2023-11-30 20:03:08.7429+00	2023-11-30 20:03:10.851916+00	TST000014	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	finished	storage	0.00	00:00:02	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2336e1f5-471b-4267-827b-5a9a9847a928	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
c43bd220-72a5-4291-9083-148dfbce2d85	2023-11-30 20:08:08.730889+00	2023-11-30 20:08:08.733139+00	2023-11-30 20:08:10.804577+00	TST000015	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	finished	storage	0.00	00:00:02	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2336e1f5-471b-4267-827b-5a9a9847a928	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
0fef2cee-09eb-4b78-a4bb-2754d93f7525	2023-11-30 20:15:08.747331+00	2023-11-30 20:15:08.749882+00	2023-11-30 20:20:10.858879+00	TST000016	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	finished	storage	0.00	00:05:02	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2336e1f5-471b-4267-827b-5a9a9847a928	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
94055b0c-ad16-42c5-a477-2c94cf82a3dd	2023-12-11 19:28:58.557481+00	2023-12-11 19:28:59.303024+00	2023-12-11 19:29:25.588841+00	TST000017	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	7036	\N	finished	rental	\N	\N	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	c90308b9-24db-4f17-b397-d9a477f0031d	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
042c6cb9-b02f-4f07-8b1c-831228aae0c6	2023-12-11 19:30:34.66636+00	2023-12-11 19:30:35.398969+00	2023-12-11 19:32:16.877309+00	TST000018	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2390	\N	finished	rental	0.00	00:01:41	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	c90308b9-24db-4f17-b397-d9a477f0031d	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
b2e0f07e-dce8-4ccc-a2cb-9cf7d527bb66	2023-12-11 19:32:28.287586+00	2023-12-11 19:32:29.000164+00	2023-12-11 19:32:49.044983+00	TST000019	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	3981	\N	finished	rental	\N	\N	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	c90308b9-24db-4f17-b397-d9a477f0031d	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
7b8c03a3-5187-482d-9208-2dee64f9a387	2024-03-22 16:14:52.896434+00	2024-03-22 16:14:53.003017+00	2024-03-22 16:15:18.355605+00	QRG000020	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	finished	storage	0.00	00:00:25	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
bcfd9e8c-2a73-4021-bed0-e524eeb6c175	2024-03-22 17:47:28.264561+00	2024-03-22 17:50:25.389069+00	2024-03-22 17:50:47.665324+00	QRG000021	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	8700	\N	finished	rental	0.00	00:00:22	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
7d421e74-ab8a-4016-ab13-34cd9c7d50bd	2024-03-22 17:53:58.519606+00	2024-03-22 17:54:11.114388+00	2024-03-22 17:54:31.641569+00	QRG000022	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	1087	\N	finished	rental	0.00	00:00:20	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
9df6b99c-1533-4765-a4b9-f651b97bae03	2024-03-22 18:06:43.18526+00	2024-03-22 18:06:55.709932+00	2024-03-22 18:07:05.457059+00	QRG000030	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	9547	\N	finished	rental	0.00	00:00:09	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
6489b2e7-e8d2-4468-8c5a-d6ae85b46bf4	2024-03-22 17:55:49.555356+00	2024-03-22 17:56:04.224795+00	2024-03-22 17:56:14.386506+00	QRG000023	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	9295	\N	finished	rental	0.00	00:00:10	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
92a3f7aa-3c32-450b-9b4a-1c882a74311d	2024-03-22 17:57:14.617641+00	2024-03-22 17:57:27.189579+00	2024-03-22 17:57:36.294034+00	QRG000024	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	1432	\N	finished	rental	0.00	00:00:09	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
a63f2aca-9bd3-4afa-a0df-ca7402d0fda8	2024-03-22 17:59:23.040181+00	2024-03-22 17:59:36.426636+00	2024-03-22 17:59:43.912724+00	QRG000025	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	8265	\N	finished	rental	0.00	00:00:07	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
063a3404-0ca3-4ea3-bbcf-806445602d5d	2024-03-22 18:08:05.665121+00	2024-03-22 18:08:18.807878+00	2024-03-22 18:08:30.179931+00	QRG000031	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	9282	\N	finished	rental	0.00	00:00:11	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
7747b6af-15cf-4685-a891-da39982235c7	2024-03-22 18:00:46.179572+00	2024-03-22 18:01:01.86535+00	2024-03-22 18:01:10.045267+00	QRG000026	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	6239	\N	finished	rental	0.00	00:00:08	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
2d4d125a-2449-43f2-b001-14738b01eb9b	2024-03-22 18:02:27.06267+00	2024-03-22 18:02:41.131703+00	2024-03-22 18:02:51.50989+00	QRG000027	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2402	\N	finished	rental	0.00	00:00:10	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
45539963-cacd-443b-acd7-e10a745cc99b	2024-03-22 18:03:48.193526+00	2024-03-22 18:04:03.554033+00	2024-03-22 18:04:16.449144+00	QRG000028	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	1970	\N	finished	rental	0.00	00:00:12	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
3a336395-8261-4fb5-a4f9-2f56d257dc37	2024-03-22 18:11:14.794499+00	2024-03-22 18:11:27.716943+00	2024-03-22 18:11:40.190031+00	QRG000032	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	5628	\N	finished	rental	0.00	00:00:12	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
78e1d498-1a90-44e4-b561-8e0c10ff0c69	2024-03-22 18:05:10.670019+00	2024-03-22 18:05:23.913824+00	2024-03-22 18:05:34.343626+00	QRG000029	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	6105	\N	finished	rental	0.00	00:00:10	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
2e6e5526-d2eb-4201-aefe-cf37c51e29ea	2024-03-22 18:12:34.01416+00	2024-03-22 18:12:47.771306+00	2024-03-22 18:12:58.570651+00	QRG000033	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	7124	\N	finished	rental	0.00	00:00:10	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/e01f5e7144e847e5ae322a616a2bcb9f.png	\N	\N	\N	\N	\N	\N	\N	\N
ac66c63a-0f35-4ad5-abe3-d56a73601934	2023-09-30 02:16:05.365288+00	2023-09-30 02:16:06.991625+00	2024-03-26 19:16:23.321252+00	TST000001	order_id	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	delivery	0.00	4289:00:16	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2c006625-1907-414d-8aca-60445d38835f	0d295146-4e10-439e-a545-d4c93ee94c2b	\N	\N	\N	\N	\N	\N	\N	\N	\N
b557bbba-296e-4c94-8c31-a7b49c70bd3d	2023-10-24 18:22:15.351756+00	2023-10-24 18:22:16.855471+00	2024-03-26 19:17:45.883395+00	TST000004	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	delivery	\N	3696:55:28	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2c006625-1907-414d-8aca-60445d38835f	0d295146-4e10-439e-a545-d4c93ee94c2b	\N	\N	\N	\N	\N	\N	\N	\N	\N
d4a6607b-3b8a-477d-8e66-28ae8854e831	2023-11-08 15:55:28.402674+00	2023-11-08 15:55:29.816159+00	2024-04-16 19:03:10.198776+00	TST000007	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	delivery	\N	3843:07:40	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2c006625-1907-414d-8aca-60445d38835f	0d295146-4e10-439e-a545-d4c93ee94c2b	\N	\N	\N	\N	\N	\N	\N	\N	\N
7b9f1684-0de8-44f0-a7d6-a1a3455d60a6	2024-05-23 16:15:18.116144+00	2024-05-23 16:15:18.748871+00	2024-05-23 16:16:31.093803+00	QRG000037	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	finished	delivery	\N	00:01:12	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	3041	\N	\N	\N	\N	\N	\N	\N
7b573bb3-d2b6-43a6-9d49-8bd07d113446	2024-05-30 20:42:00.229642+00	2024-05-30 20:43:07.609617+00	2024-05-30 20:44:01.242346+00	QRG000038	\N	pi_3PMFpMD5DngcLH8R03CyQcVD	seti_1PMFnPD5DngcLH8RYa3nv6te	\N	\N	\N	\N	\N	\N	\N	6424	\N	finished	rental	0.50	00:00:53	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
2e4021d3-f7a7-4692-9adf-65c787504177	2024-06-03 13:59:39.976972+00	2024-06-03 13:59:50.557934+00	2024-06-03 14:00:09.611042+00	QRG000042	\N	pi_3PNbQiD5DngcLH8R0PONvV01	seti_1PNbQGD5DngcLH8Rtsnw8Flf	\N	\N	\N	\N	\N	\N	\N	7931	\N	finished	rental	0.50	00:00:19	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
33dc0254-93c7-4e6e-928e-78b32b3c074e	2024-06-03 13:56:07.19944+00	2024-06-03 13:56:19.074811+00	2024-06-03 13:57:23.48587+00	QRG000040	\N	\N	seti_1PNbMpD5DngcLH8RO923jLVJ	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	rental	\N	00:01:04	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
2fa25128-bbfa-42c5-b7e9-f5ee6611e9a6	2024-06-03 13:51:23.146605+00	2024-06-03 13:52:44.816059+00	2024-06-03 13:55:57.554593+00	QRG000039	\N	\N	seti_1PNbIFD5DngcLH8RLbzRNMuG	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	rental	\N	00:03:12	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
39f24cf3-3091-497b-94d2-f96a55358cf5	2024-06-03 13:57:32.619879+00	2024-06-03 13:57:43.871825+00	2024-06-03 13:59:32.317727+00	QRG000041	\N	\N	seti_1PNbODD5DngcLH8RhqUlAW8u	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	rental	\N	00:01:48	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
0fe54699-90a4-49d2-aaa2-a5ef1997e5b5	2024-06-03 17:25:22.615432+00	2024-06-03 17:26:00.031719+00	2024-06-03 17:27:19.718598+00	QRG000043	\N	pi_3PNefCD5DngcLH8R0Eg2XDdB	seti_1PNedLD5DngcLH8RWMjraKIt	\N	\N	\N	\N	\N	\N	\N	9492	\N	finished	rental	30.00	00:01:19	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	7081ec4b-9913-453e-973a-7afb9e795ab5	\N	\N	\N	\N	\N	\N
d6deddb6-18b9-4fec-a0b4-8bb4be1650bc	2024-06-03 17:28:54.197516+00	2024-06-03 17:29:31.876289+00	2024-06-03 17:30:53.636908+00	QRG000044	\N	pi_3PNeieD5DngcLH8R1UvPzbFf	seti_1PNegkD5DngcLH8RZxwi2x8g	\N	\N	\N	\N	\N	\N	\N	1117	\N	finished	rental	30.00	00:01:21	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	7081ec4b-9913-453e-973a-7afb9e795ab5	\N	\N	\N	\N	\N	\N
433477e1-6d04-4ae9-a25f-8733dc859d4d	2024-06-03 17:32:26.514499+00	2024-06-03 17:33:01.625308+00	2024-06-03 17:33:11.298497+00	QRG000045	\N	pi_3PNeksD5DngcLH8R1SFv3Vhn	seti_1PNekBD5DngcLH8R6pDca43h	\N	\N	\N	\N	\N	\N	\N	3591	\N	finished	rental	15.00	00:00:09	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	7081ec4b-9913-453e-973a-7afb9e795ab5	\N	\N	\N	\N	\N	\N
3a470c2f-fa41-4082-9daa-3c53be28994c	2024-06-03 17:33:36.0664+00	2024-06-03 17:34:04.900686+00	2024-06-03 17:35:07.902048+00	QRG000046	\N	pi_3PNemkD5DngcLH8R1VxjbEF8	seti_1PNelID5DngcLH8RA33mPXzK	\N	\N	\N	\N	\N	\N	\N	8452	\N	finished	rental	15.00	00:01:02	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	7081ec4b-9913-453e-973a-7afb9e795ab5	\N	\N	\N	\N	\N	\N
1e441b74-db44-4394-8e40-f2757c72d762	2024-03-26 19:16:34.329781+00	2024-03-26 19:16:35.003237+00	2024-06-19 15:52:59.772623+00	QRG000035	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	delivery	\N	2036:36:24	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	0d295146-4e10-439e-a545-d4c93ee94c2b	\N	\N	\N	\N	\N	\N	\N	\N	\N
16b1d4ec-e777-4db6-8d8f-58235ccc967d	2024-06-18 14:25:03.041306+00	2024-06-18 14:25:49.70778+00	2024-06-18 14:31:12.824427+00	QRG000047	\N	pi_3PT33zD5DngcLH8R1ryySg4P	seti_1PT2y3D5DngcLH8Rw5RrqPEJ	\N	\N	\N	\N	\N	\N	\N	1102	\N	finished	rental	180.00	00:05:23	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
534990c5-1dbb-49a9-b9a1-7b0eb9635cb9	2024-06-18 14:33:45.808868+00	2024-06-18 14:34:11.667536+00	2024-06-18 14:37:10.892212+00	QRG000048	\N	pi_3PT39lD5DngcLH8R1wXKC18M	seti_1PT36UD5DngcLH8RGKWg6Cv9	\N	\N	\N	\N	\N	\N	\N	6062	\N	finished	rental	90.00	00:02:59	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
524be014-7580-453a-b4dd-5dda1c344dc3	2024-06-18 16:30:57.623917+00	2024-06-18 16:31:07.510524+00	2024-06-18 16:32:31.690163+00	QRG000058	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	1337	\N	finished	rental	0.00	00:01:24	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
813c95ea-4006-492f-b62f-0c4c4ba7840b	2024-06-18 14:38:57.248442+00	2024-06-18 14:39:29.095971+00	2024-06-18 14:41:10.682559+00	QRG000049	\N	pi_3PT3DdD5DngcLH8R0CRKmqkl	seti_1PT3BVD5DngcLH8RAIDxr4jh	\N	\N	\N	\N	\N	\N	\N	8217	\N	finished	rental	60.00	00:01:41	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
29200705-c237-4a0a-b5ee-4fb171d35cdf	2024-06-18 14:49:37.916106+00	2024-06-18 14:51:03.267475+00	2024-06-18 14:51:21.08868+00	QRG000050	\N	pi_3PT3NUD5DngcLH8R1aefah3R	seti_1PT3LsD5DngcLH8R2uBauYGj	\N	\N	\N	\N	\N	\N	\N	4621	\N	finished	rental	30.00	00:00:17	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
465cd161-4473-47fe-9f67-defe90562b76	2024-06-18 15:19:33.220698+00	2024-06-18 15:20:02.111216+00	2024-06-19 15:45:41.829291+00	QRG000057	\N	\N	seti_1PT3ooD5DngcLH8RTnt0FPVs	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	rental	\N	24:25:39	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
5ff649c1-9321-426a-a3ac-216aeca42317	2024-06-18 14:54:55.609223+00	2024-06-18 14:55:32.180497+00	2024-06-18 14:56:51.429055+00	QRG000052	\N	pi_3PT3SoD5DngcLH8R0PXVzsXc	seti_1PT3QyD5DngcLH8RGz9LmXZW	\N	\N	\N	\N	\N	\N	\N	7045	\N	finished	rental	60.00	00:01:19	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
58e1f666-a7db-42b5-a26f-71a12802d4a1	2024-03-26 19:17:56.675863+00	2024-03-26 19:17:57.345207+00	2024-06-19 15:50:56.482672+00	QRG000036	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	delivery	\N	2036:32:59	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	0d295146-4e10-439e-a545-d4c93ee94c2b	\N	\N	\N	\N	\N	\N	\N	\N	\N
a878225d-5268-42bb-a22a-ca8c5e1f3f91	2024-06-18 16:58:03.107296+00	2024-06-18 16:58:12.954+00	2024-06-19 15:53:29.702233+00	QRG000060	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	rental	0.00	22:55:16	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
b82f48f9-07b4-4b2e-bc2c-4af5e0678056	2024-06-18 14:59:42.607611+00	2024-06-18 15:00:11.20653+00	2024-06-18 15:00:23.163618+00	QRG000053	\N	pi_3PT3WED5DngcLH8R03zXhojB	seti_1PT3VbD5DngcLH8RxXrjZZNm	\N	\N	\N	\N	\N	\N	\N	1243	\N	finished	rental	30.00	00:00:11	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
5cfdc92d-9151-4882-bb8d-2e7e2ab6a681	2024-06-18 15:04:06.852685+00	2024-06-18 15:04:35.588101+00	2024-06-18 15:04:49.515487+00	QRG000054	\N	pi_3PT3aWD5DngcLH8R1RI41XeU	seti_1PT3ZrD5DngcLH8Rv2Mk0wR8	\N	\N	\N	\N	\N	\N	\N	3446	\N	finished	rental	30.00	00:00:13	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
f85b1008-793d-4123-8c84-8fcf1fc803e5	2024-06-18 15:08:41.016058+00	2024-06-18 15:09:17.02248+00	2024-06-18 15:09:36.514573+00	QRG000055	\N	pi_3PT3f9D5DngcLH8R0QaOjdds	seti_1PT3eHD5DngcLH8RhdO05xPf	\N	\N	\N	\N	\N	\N	\N	7353	\N	finished	rental	30.00	00:00:19	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
89b77e04-7413-4ece-8a60-6c0b5df9e645	2024-06-18 15:11:51.015323+00	2024-06-18 15:12:25.946127+00	2024-06-18 15:14:09.834827+00	QRG000056	\N	pi_3PT3jYD5DngcLH8R1vakKM4s	seti_1PT3hLD5DngcLH8Rqlb0fRwL	\N	\N	\N	\N	\N	\N	\N	7600	\N	finished	rental	60.00	00:01:43	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
bd248b61-a2ea-47e4-b722-f1b6a07f0010	2024-03-26 19:14:40.267765+00	2024-03-26 19:14:40.935572+00	\N	QRG000034	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	3356	\N	awaiting_service_dropoff	delivery	\N	\N	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	0d295146-4e10-439e-a545-d4c93ee94c2b	\N	\N	\N	12.00	damaged_items	\N	\N	\N	\N
62a82393-d228-4538-9d6e-8b1d298e23a4	2024-06-18 16:34:34.469892+00	2024-06-18 16:34:45.071829+00	2024-06-18 16:55:16.832093+00	QRG000059	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2846	\N	finished	rental	0.00	00:20:31	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	12.00	damaged_items	\N	\N	\N	\N
efdd57f4-d090-476e-8bc0-8e2bc26b8b43	2024-06-24 16:13:51.395214+00	2024-06-24 16:13:59.133451+00	2024-06-25 18:12:41.561973+00	QRG000067	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2957	\N	finished	rental	0.00	25:58:42	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
aec3d2f3-7e96-4e64-9f6c-9c6e3f96dfa1	2024-06-21 16:55:34.642925+00	2024-06-21 16:56:03.084386+00	2024-06-21 16:59:43.46937+00	QRG000062	\N	pi_3PUAlUD5DngcLH8R18zsCS9a	seti_1PUAkND5DngcLH8RdrgaMiSH	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	service	27.60	00:03:40	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	2.30	\N	\N	\N
a13a6a68-2072-4342-8ab6-0e3c346731cb	2024-06-25 18:19:07.235145+00	2024-06-25 18:19:16.999905+00	2024-06-25 18:20:22.0815+00	QRG000068	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	3742	\N	finished	rental	0.00	00:01:05	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
e358425f-98bf-4d6e-9880-ea1dce3e6c1e	2024-06-21 16:59:56.45553+00	2024-06-21 17:00:29.051195+00	2024-06-25 19:24:51.748504+00	QRG000063	\N	pi_3PUApXD5DngcLH8R1moId4YE	seti_1PUAoaD5DngcLH8R3N7PLNcT	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	service	27.60	98:24:22	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	2.30	\N	\N	\N
46968bbf-7bad-471e-81b4-781b08ae659a	2024-06-25 19:25:35.54464+00	2024-06-25 19:25:35.546867+00	2024-06-25 19:25:35.546869+00	QRG000069	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	finished	vending	\N	\N	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
57aad799-5289-4808-b3e3-a60992abf0de	2024-06-21 17:18:32.606099+00	2024-06-21 17:19:00.548598+00	2024-06-21 17:20:04.292562+00	QRG000064	\N	\N	seti_1PUB6bD5DngcLH8RHmhdfYXA	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	service	\N	00:01:03	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
cf714aba-5344-4cae-a603-af19db46cf27	2024-06-26 13:54:29.871497+00	2024-06-26 13:54:29.874051+00	2024-06-26 13:54:29.874052+00	QRG000070	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	finished	vending	\N	\N	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
b48e5bde-bc9d-449d-b83f-59f0c46a1ddf	2024-06-19 18:47:29.583827+00	2024-06-19 18:47:29.586731+00	2024-06-24 15:53:51.781773+00	QRG000061	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	finished	storage	0.00	117:06:22	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	12.00	damaged_items	\N	\N	\N	\N
cedc9cce-a73a-4fca-b015-83807401cd83	2024-06-24 16:10:09.149109+00	2024-06-24 16:10:18.818239+00	2024-06-24 16:13:19.135373+00	QRG000066	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	6675	\N	finished	rental	0.00	00:03:00	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N	\N	\N	\N	\N	\N	\N	\N	\N
b42de1c6-69cc-4349-8536-ae1c2d82cc23	2024-06-21 17:20:12.74088+00	2024-06-21 17:20:39.501492+00	2024-06-25 18:14:48.28623+00	QRG000065	\N	pi_3PVbtkD5DngcLH8R1yArrMxU	seti_1PUB8DD5DngcLH8RkYanKjng	\N	\N	\N	\N	\N	\N	\N	\N	\N	refunded	service	264.00	96:54:08	1.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	22.00	\N	\N	\N
b0011fdb-d441-4e25-8a85-598aa568f3d6	2024-07-30 16:10:08.696744+00	2024-07-30 16:10:08.699591+00	2024-07-30 16:11:01.733758+00	QRG000071	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	1234	canceled	storage	\N	00:00:53	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	f83ef364-0b12-4c39-a8c9-27c10f1d32d7	\N	\N	\N	\N	\N	\N	2024-07-30 16:11:01.733759+00	API	\N
ce3c7376-9819-448c-88ad-1e463baa8bea	2024-07-30 16:11:54.516962+00	2024-07-30 16:11:54.51904+00	\N	QRG000072	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	in_progress	storage	\N	\N	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2c006625-1907-414d-8aca-60445d38835f	f83ef364-0b12-4c39-a8c9-27c10f1d32d7	\N	\N	\N	\N	\N	\N	\N	\N	\N
0027c524-5ef0-412a-8169-264c11462f49	2024-07-31 17:48:14.147165+00	2024-07-31 17:48:14.150404+00	2024-07-31 17:48:14.150406+00	QRG000073	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	finished	vending	\N	\N	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2c006625-1907-414d-8aca-60445d38835f	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
923c48fb-1a00-4a41-b70c-4305b9677711	2024-08-06 13:24:19.113361+00	2024-08-06 13:24:20.505817+00	2024-08-06 13:29:03.965236+00	QRG000074	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	canceled	delivery	\N	00:04:43	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2c006625-1907-414d-8aca-60445d38835f	ec63afe1-098a-4170-9fde-27b72e2c6125	\N	\N	\N	\N	\N	\N	2024-08-06 13:29:03.965237+00	API	\N
dc6107b6-a859-40fc-9f52-073f8fccaf34	2024-08-06 13:29:36.236323+00	2024-08-06 13:29:37.607412+00	\N	QRG000075	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	awaiting_service_dropoff	delivery	\N	\N	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2c006625-1907-414d-8aca-60445d38835f	ec63afe1-098a-4170-9fde-27b72e2c6125	\N	\N	\N	\N	\N	\N	\N	\N	\N
d9f7d374-2d13-45ad-82b6-e2af2a113777	2024-06-18 14:52:30.32914+00	2024-06-18 14:53:01.305174+00	2024-06-18 14:53:27.286355+00	QRG000051	\N	pi_3PT3PWD5DngcLH8R1LJkJ22j	seti_1PT3OcD5DngcLH8RHrflwVmy	\N	\N	\N	\N	\N	\N	\N	999999	\N	finished	rental	30.00	00:00:25	0.00	\N	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N	\N	\N	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: feedback; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.feedback (id, id_org, id_location, id_device, member, department, image, description, notes) FROM stdin;
c60cf5b3-ae7c-4b13-98ca-664de0227a5a	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	\N	Eduardo Alvarez	\N	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/8bd31eb5fa9e43a7b6469e6be5690de0.png	Good stuff	Test
7da9f00a-e3ba-472c-8b3c-fd634ac66135	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	\N	Eduardo Alvarez	\N	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/fc32561706ce42a08ddb894f6b60ee2d.png	Good stuff	Test
5c6fcf1f-4d68-4abc-b69b-68a741664592	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	\N	Eduardo Alvarez	sales	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/c4b3a022e5a3426e8bb11089662d2870.png	Good stuff	Test
\.


--
-- Data for Name: groups; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.groups (id, created_at, name, id_org) FROM stdin;
6c922138-5400-473b-b949-19982ecc212d	2023-05-12 16:01:45.824438	Koloni Group	bc6647fb-90d8-4c79-87e9-9b6942383e4a
\.


--
-- Data for Name: harbor_events; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.harbor_events (id, tower_id, locker_id, pin_code, status) FROM stdin;
52e4710f-4ede-469d-8855-62c7c650de11	0100000000000014	362	8378	finished
9ed66a63-bada-4282-8b5e-33a1fee446bc	0100000000000014	373	2553	finished
\.


--
-- Data for Name: issue; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.issue (id, created_at, pictures, issue_id, description, status, id_org, id_user, id_event, team_member_id) FROM stdin;
b669295c-d849-49e9-9aee-1db0ce504a32	2023-01-18 00:43:02.067359+00	\N	\N	wfvaewfvaefwv	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	ac66c63a-0f35-4ad5-abe3-d56a73601934	\N
d5952509-2c2a-4a03-b1b9-b45e9c249fce	2023-11-14 15:34:30.228866+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/0317f66105774deea05daaaedac8ec00.jpg}	ISS372430	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
18049175-f7a6-4255-83ae-1d6b1523ae62	2023-11-14 15:38:51.030402+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/64a60bc2026a49ce8e22ace6157bfaee.jpg}	ISS703816	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
5a8be54c-9bc7-49de-8a05-fb5d2e9d8e65	2023-11-14 15:39:40.85026+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/60e58aa901614b16800f4b1d36a45db3.jpg}	ISS090446	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
c19769ff-fdb6-4481-95a6-5ed868741439	2023-11-14 15:41:25.075871+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/9f208cf31c1b4a25be6e4317ccbd8c56.jpg}	ISS336885	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
5c13557c-ddf3-4a66-a71b-f1116dba97b3	2023-11-14 15:42:46.966815+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/93221dacc8134ad0a77abf054a82a29a.jpg}	ISS821817	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
f269a564-3cf9-4dca-a1c6-cb01f5fa8a7f	2023-11-14 15:43:06.670867+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/ed19c525bbb94b46974acaa7d32ae7de.jpg}	ISS826128	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
73f0fc23-3005-4eb6-a83a-e9ba703938a4	2023-11-14 15:44:41.239223+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/eba42a33b1a74915a803bb8dcfe42a7d.jpg}	ISS765409	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
0c511b3c-cbcc-498b-9d1e-b8619c1123be	2023-11-14 15:49:30.766514+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/f8ae5fd016fe4e1a97d9e76df837a01d.jpg}	ISS475163	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
e1b28fa3-0f52-4524-ad71-65737b169cff	2023-11-14 15:52:11.356005+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/335ffb77d3d148bcb642ebba476ea586.jpg}	ISS477759	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
5cbd525b-9e24-4a3f-9df5-fd05ce1375bf	2023-11-14 15:55:06.087659+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/8c0b89ea533744db94e0874445e182e0.jpg}	ISS805583	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
ed9c4acd-bcd3-4eec-b916-e710c807d226	2023-11-14 15:59:12.836609+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/96e7eedf58674341b898183043d00a71.jpg}	ISS204844	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
5b97e979-865b-4f5a-b564-8891b97d7a35	2023-11-14 16:02:07.296524+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/e30b514221014627b8a0fff0f1f10149.jpg}	ISS089210	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
1954513b-58f1-4e2e-bfb8-7ee602695df3	2023-11-14 16:03:37.271088+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/2259cc6b1f004906967a1012d2f0c85d.jpg}	ISS183539	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
3c17468a-45d6-4982-b972-0f076ee66eb0	2023-11-14 16:11:50.522496+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/a1c0d40e9199495eb5ec32f7032acd60.jpg}	ISS235514	I need help!	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	\N
6a6b2e9a-2e04-49d2-a6e1-d0de6df873a7	2023-11-14 15:37:43.487374+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/5115473c54194d389b24e923a4898ae2.jpg}	ISS887433	Testing away	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	9b836bd4-ec75-446b-a96a-b2f8957ae98a	d4a6607b-3b8a-477d-8e66-28ae8854e831	e3dc711e-1197-4f34-aaa9-441c22953d76
7143442e-0848-4bcf-ab9b-4a08ffbb7bc4	2023-11-14 16:13:20.640982+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/64f997513950476f99500555945bab83.jpg}	ISS155544	Help is needed	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	0c508cf5-797a-46f4-b379-5fb23268c789	d4a6607b-3b8a-477d-8e66-28ae8854e831	e3dc711e-1197-4f34-aaa9-441c22953d76
9b3d32e8-26a3-474b-a9c2-6ab828a430e6	2024-04-16 19:02:52.891391+00	{https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/3940654cc31e4de18dec67296080cacb.png}	ISS559242	Test	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	ab292219-76e8-47a7-8dc8-778778613a84	d4a6607b-3b8a-477d-8e66-28ae8854e831	7bfde0e2-713b-45d1-a2fe-7a64ab4b7b44
179e8f47-48c1-453e-b68f-66e3d7c983c7	2024-06-19 15:45:38.096211+00	\N	ISS137276	Test put in maintenance	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	465cd161-4473-47fe-9f67-defe90562b76	\N
ae06202e-e527-4b7c-a57b-01431e3681ad	2024-06-19 15:50:53.184406+00	\N	ISS489227	Test issue NON MAINTENANCE	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	58e1f666-a7db-42b5-a26f-71a12802d4a1	\N
fc1ff01b-57ba-40cc-af69-3de77ff278eb	2024-06-19 15:52:56.40165+00	\N	ISS701011	Test issue NON MAINTENANCE	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	1e441b74-db44-4394-8e40-f2757c72d762	\N
b218b4a7-c303-4994-a40d-c6fb35a61532	2024-06-19 15:53:26.510757+00	\N	ISS718472	Test issue NON MAINTENANCE	pending	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	a878225d-5268-42bb-a22a-ca8c5e1f3f91	\N
\.


--
-- Data for Name: link_device_price; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.link_device_price (id, id_device, id_price) FROM stdin;
b76b628d-a24a-49ad-9748-551319701573	7144fcf6-ce2b-47b8-afe3-58381c2449fc	a19f25e9-4743-4174-95bd-510e9f25edc4
21e1daff-5697-465e-ba7d-9db11f512b8e	7144fcf6-ce2b-47b8-afe3-58381c2449fc	18f26bc8-c006-4049-b709-b2250cb66eed
\.


--
-- Data for Name: link_groups_devices; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.link_groups_devices (id, id_group, id_device) FROM stdin;
5ff49eb5-93ca-445c-b4d9-35ae0a68b121	6c922138-5400-473b-b949-19982ecc212d	ec63afe1-098a-4170-9fde-27b72e2c6125
\.


--
-- Data for Name: link_groups_locations; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.link_groups_locations (id, id_group, id_location) FROM stdin;
\.


--
-- Data for Name: link_groups_user; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.link_groups_user (id, id_group, id_user) FROM stdin;
c37fddb8-a062-4d61-bd79-70f38b882672	6c922138-5400-473b-b949-19982ecc212d	e8442381-7053-411c-9c43-1458ca7b18a2
\.


--
-- Data for Name: link_member_location; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.link_member_location (id, user_id, id_location) FROM stdin;
\.


--
-- Data for Name: link_membership_location; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.link_membership_location (id, id_membership, id_location) FROM stdin;
8290c362-84ed-43ce-a0cf-ee301119d4da	4814e2aa-0682-4d0d-9c03-ff7f3618ed66	7cdfd8cd-842d-4682-b634-965ab7f4ed44
\.


--
-- Data for Name: link_notification_location; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.link_notification_location (id, id_notification, id_location) FROM stdin;
\.


--
-- Data for Name: link_org_user; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.link_org_user (created_at, id_org, id_user, id_membership, id_favorite_location, stripe_customer_id, stripe_subscription_id) FROM stdin;
2023-04-12 14:28:14.327991+00	fec27db7-466a-48a1-956b-cbfd7c9eb9d9	0c508cf5-797a-46f4-b379-5fb23268c789	\N	\N	\N	\N
2023-09-28 14:28:14.327991+00	bc6647fb-90d8-4c79-87e9-9b6942383e4a	796efd9e-cfd0-4347-b25e-30de3099f2ea	\N	\N	\N	\N
2023-04-12 14:28:14.327991+00	fec27db7-466a-48a1-956b-cbfd7c9eb9d9	2336e1f5-471b-4267-827b-5a9a9847a928	\N	\N	\N	\N
2023-09-28 14:28:14.327991+00	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2336e1f5-471b-4267-827b-5a9a9847a928	\N	\N	\N	\N
2023-06-29 17:47:49.289925+00	bc6647fb-90d8-4c79-87e9-9b6942383e4a	ab292219-76e8-47a7-8dc8-778778613a84	\N	\N	\N	\N
2023-10-24 18:19:09.835868+00	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2c006625-1907-414d-8aca-60445d38835f	\N	7cdfd8cd-842d-4682-b634-965ab7f4ed44	\N	\N
2024-01-18 14:19:55.330356+00	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	\N	\N	cus_QCf7no6LNYAcYF	\N
\.


--
-- Data for Name: link_user_devices; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.link_user_devices (id, id_user, id_device) FROM stdin;
\.


--
-- Data for Name: link_user_locations; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.link_user_locations (id, id_user, id_location) FROM stdin;
\.


--
-- Data for Name: lite_app_settings; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.lite_app_settings (id, id_org, sign_in_method, allow_multiple_rentals, allow_user_reservation, track_product_condition, allow_photo_end_rental, setup_in_app_payment, primary_color, secondary_color) FROM stdin;
\.


--
-- Data for Name: location; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.location (id, created_at, hidden, contact_email, contact_phone, name, custom_id, address, image, latitude, longitude, restrict_by_user_code, verify_pin_code, verify_qr_code, verify_url, verify_signature, email, phone, id_org, id_price, shared) FROM stdin;
7cdfd8cd-842d-4682-b634-965ab7f4ed44	2023-04-20 15:40:15.498146+00	f	\N	\N	Some Location	\N	Some Address	\N	92.123123000000000	91.123123000000000	f	t	f	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	f
235952ea-2af0-4ce9-91a0-0164f5857e13	2023-05-04 19:29:31.161565+00	f	\N	\N	Test Location	\N	Test Name	\N	32.312312300000000	32.123123123000000	f	t	f	f	f	f	t	fec27db7-466a-48a1-956b-cbfd7c9eb9d9	\N	f
2d573dc0-c92c-4007-82e4-28d8e7422686	2023-05-04 19:29:47.603033+00	f	\N	\N	Luxemburg	\N	Test Name	\N	32.312312300000000	32.123123123000000	f	t	f	f	f	f	t	fec27db7-466a-48a1-956b-cbfd7c9eb9d9	\N	f
880a7720-e92c-4395-a614-fbc61cbf5dfb	2023-04-11 21:19:59.443077+00	f	\N	\N	Test Location 	\N	Test address	\N	43.123456700000000	43.123456700000000	t	t	f	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	f
24346412-25e3-408d-928a-d416d5fd034f	2023-05-11 18:06:11.989925+00	f	\N	\N	Custom ID Test	TRAX_01	Antlanta, USA	\N	32.232300000000000	32.232300000000000	f	t	t	t	f	t	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	f
5e27cb08-fdc8-44c7-9755-5853c3c2b5b1	2023-11-27 17:00:39.486273+00	f	\N	\N	test pricey	\N	123 main	\N	32.123000000000000	32.123000000000000	f	t	f	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	35a147d1-114b-46a5-8c61-46ec52c89448	f
200e3b54-c72b-40ed-8993-f608d21c2bb2	2023-01-31 14:10:43.371919+00	f	\N	\N	Luxemburg	\N	Boulevard Street	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/81c797583cea4c16bde8c3d3120c954a.jpg	32.134553000000000	52.123453000000000	f	t	f	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	t
\.


--
-- Data for Name: locker_wall; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.locker_wall (lockers, id, created_at, image, name, description, custom_id, qty_wide, qty_tall, is_kiosk, id_org, id_location) FROM stdin;
[{"x": 1, "y": 1, "id": "0d295146-4e10-439e-a545-d4c93ee94c2b", "kiosk": false}, {"x": 1, "y": 2, "id": "ec63afe1-098a-4170-9fde-27b72e2c6125", "kiosk": false}, {"x": 2, "y": 1, "id": null, "kiosk": true}]	c4bfcd60-50e1-4b40-a7a0-ffa97f4c9446	2023-10-04 17:50:47.12549	\N	Timmy		\N	3	4	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
[{"x": 1, "y": 1, "id": "7144fcf6-ce2b-47b8-afe3-58381c2449fc", "kiosk": false}]	5c38c5a1-8442-4443-8f93-36460b647e1c	2023-12-13 15:37:32.931192	\N	Testt	Test	\N	2	1	f	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
\.


--
-- Data for Name: log; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.log (id, id_org, created_at, id_event, id_device, log_owner, log_type) FROM stdin;
8178d468-0c5d-4ea7-8704-56c4008a8cf1	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2024-07-17 14:05:41.607076+00	\N	7144fcf6-ce2b-47b8-afe3-58381c2449fc	API	unlock
33280a47-a0f2-442e-b02b-72b2b98326a6	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2024-07-31 17:48:16.370042+00	\N	7144fcf6-ce2b-47b8-afe3-58381c2449fc	API	unlock
afdb0c02-7891-4c0e-8f21-50e3c46007ad	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2024-07-31 17:48:19.941436+00	\N	7144fcf6-ce2b-47b8-afe3-58381c2449fc	API	report_issue
\.


--
-- Data for Name: memberships; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.memberships (id, created_at, expires_at, name, description, active, currency, amount, billing_type, billing_period, number_of_payments, membership_type, value, stripe_product_id, stripe_price_id, id_org) FROM stdin;
c6953642-9a93-4ed7-8108-405266dd5911	2023-05-17 17:40:22.111148+00	\N	Test Membership	Just some test membership, nothing to see here	t	usd	5.00	recurring	month	0	limited	5	prod_NudcSfmFpgfvkc	price_1NMCyuRYPikDAtvX3iRHBAI8	bc6647fb-90d8-4c79-87e9-9b6942383e4a
4814e2aa-0682-4d0d-9c03-ff7f3618ed66	2023-07-20 18:49:48.886344+00	\N	Test locations	Another Description	t	usd	14.00	one_time	month	3	unlimited	0	prod_OIdBLSvu109Sw1	price_1NW29DD3z7ZcgGkT742pBj1N	bc6647fb-90d8-4c79-87e9-9b6942383e4a
\.


--
-- Data for Name: notification; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.notification (id, created_at, name, message, mode, notification_type, event, time_amount, time_unit, before, after, email, sms, push, email_2nd, sms_2nd, push_2nd, is_template, id_org, id_member, recipient_type) FROM stdin;
ba506276-e529-4d06-8172-9fe7e9f46edd	2024-06-18 16:27:58.631371+00	Welcome	Welcome to ((org_name))! Thank you for signing up. You can now have ((service)) at your fingertips. Place your first order today from the app.	service	on_signup	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
e48befa3-9b4f-4827-897a-db7570bd9688	2024-06-18 16:27:59.310734+00	Picked up	Good news! Your items has been picked up and is being processed for order ((order_id)). We'll soon weigh it and let you know how much will be charged to your card.	service	on_service_pickup	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
1d6972fe-06fd-450d-8560-3bd44bdce0a0	2024-06-18 16:27:59.94576+00	Charge	Your items weigh ((weight)) ((unit)) and you were successfully charged ((currency))((amount)) for order ((order_id)). Your order is in process and we will notify you when it's available to be picked up.	service	on_service_charge	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
8d5c4436-1dcb-41fe-8aef-c7b793cff00f	2024-06-18 16:28:00.617224+00	User Pickup	Your fresh laundry is ready to be picked up in locker ((locker_number)) for  order ((order_id)). Please retrieve as soon as possible from ((location_name)). ((location_address)). Use the app to unlock the locker and retrieve your items.	service	on_service_dropoff	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
441889f5-1687-49a1-8983-d4d43666554a	2024-06-18 16:28:01.29851+00	Complete	Order ((order_id)) has been completed. Thank you for trusting us with your ((service)). Please return soon!	service	on_complete	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
1c6798de-3d8e-419a-ba89-52e867049d54	2024-06-18 16:28:01.96039+00	Welcome	Welcome to ((org_name))! Thank you for signing up. You can use our rental services hassle free and at your convenience. Start your first rental from the app.	rental	on_signup	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
cdbedd28-bcc0-46e4-8cc0-3fdf3928bd2f	2024-06-18 16:28:03.268211+00	Complete	Order ((order_id)) has successfully been completed. Thank you for using our service. Please return soon!	rental	on_complete	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
07eef0c9-11f9-4b72-91db-fb77a4da7d03	2024-06-18 16:28:03.911501+00	Welcome	Welcome to ((org_name))! Thank you for signing up. You can use our storage services hassle free and at your convenience. Start your first transaction now from the app.	storage	on_signup	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
5f32becf-fe46-4e1c-853a-7549dfcc56fd	2024-06-18 16:28:05.207773+00	Complete	Order ((order_id)) has successfully been completed. Thank you for trusting us. Please return soon! 	storage	on_complete	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
ee854ef5-6446-421c-b368-e29a5cefa87e	2024-06-18 16:28:05.848595+00	User Sign Up	Welcome to ((org_name))! Thank you for signing up. You can use our delivery services hassle free and at your convenience. Start your first delivery now from the app.	delivery	on_signup	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
72505686-7cf4-42e8-9a5c-8387a7df80d7	2024-06-18 16:28:07.115879+00	Complete	Order ((order_id)) has successfully been completed. Thank you for trusting us. Please return soon! 	delivery	on_complete	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
17c5787d-6ce8-48c3-bf00-350f820d1489	2024-06-18 16:28:02.622679+00	Transaction Starts	Order ((order_id)) has started in locker ((locker_number)) at ((location_name)). ((location_address)). Click Here to view your transaction ((URL))	rental	on_start	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
01a87ecc-6cf3-4ac7-98ed-8fc70f47906a	2024-06-18 16:28:04.557693+00	Transaction Starts	Order ((order_id)) has started in locker ((locker_number)) at ((location_name)). ((location_address)). Click Here to view your transaction ((URL))	storage	on_start	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
13b14bc3-f2c2-4fc3-af74-b98a4897fe9f	2024-06-18 16:28:06.483373+00	Transaction Starts	Order ((order_id)) has started in locker ((locker_number)) at ((location_name)). ((location_address)). Click Here to view your transaction ((URL))	rental	on_start	\N	0.00	immediately	f	t	t	t	t	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
0007cf8e-2bab-4946-99a0-5abdedd6a70f	2024-06-26 18:54:06.687272+00	Ready for pick-up	Your items are ready for pickup! Your Order ID is ((order_id)). We will update you soon when we pick them up from ((location_name))	service	on_start	\N	0.00	immediately	f	t	f	t	f	f	f	f	t	fec27db7-466a-48a1-956b-cbfd7c9eb9d9	\N	user
07afb344-998e-4bce-b8bd-b58732112f17	2024-06-26 18:54:06.687272+00	Ready for pick-up	Your items are ready for pickup! Your Order ID is ((order_id)). We will update you soon when we pick them up from ((location_name))	service	on_start	\N	0.00	immediately	f	t	f	t	f	f	f	f	t	2a36b58a-ea63-4469-a3ba-5e6c19226689	\N	user
8d827f2b-cf5e-489a-a4b5-fe4b2b2e73d4	2024-06-26 18:54:06.687272+00	Ready for pick-up	Your items are ready for pickup! Your Order ID is ((order_id)). We will update you soon when we pick them up from ((location_name))	service	on_start	\N	0.00	immediately	f	t	f	t	f	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
1e0de4e9-616f-484c-8c87-e744cafa7a43	2024-06-26 18:54:06.687272+00	Ready for pick-up	Your items are ready for pickup! Your Order ID is ((order_id)). We will update you soon when we pick them up from ((location_name))	service	on_start	\N	0.00	immediately	f	t	f	t	f	f	f	f	t	c6bad52f-f2b3-443d-b1e7-946d7e5b2641	\N	user
a1066939-61b6-4298-a113-9b5f1ac2675d	2024-06-26 18:54:06.687272+00	Ready for pick-up	Your items are ready for pickup! Your Order ID is ((order_id)). We will update you soon when we pick them up from ((location_name))	service	on_start	\N	0.00	immediately	f	t	f	t	f	f	f	f	t	b5361f54-bd98-406b-9088-ca46cab34146	\N	user
785f96f6-54e7-4e87-a78a-d45261980cd4	2024-07-05 14:22:11.482597+00	Expired Package	Your parcel is going to expire in ((selected_duration)) from ((locker_number)) at ((location_name)). If you do not collect your parcel before it expires you can collect it from the front desk.	delivery	on_expired	\N	0.00	immediately	f	t	f	t	f	f	f	f	t	fec27db7-466a-48a1-956b-cbfd7c9eb9d9	\N	user
11cddc02-41f2-4c66-8247-91dcada62b45	2024-07-05 14:22:11.482597+00	Expired Package	Your parcel is going to expire in ((selected_duration)) from ((locker_number)) at ((location_name)). If you do not collect your parcel before it expires you can collect it from the front desk.	delivery	on_expired	\N	0.00	immediately	f	t	f	t	f	f	f	f	t	2a36b58a-ea63-4469-a3ba-5e6c19226689	\N	user
9b014a10-3986-432e-a650-a24acbba8be8	2024-07-05 14:22:11.482597+00	Expired Package	Your parcel is going to expire in ((selected_duration)) from ((locker_number)) at ((location_name)). If you do not collect your parcel before it expires you can collect it from the front desk.	delivery	on_expired	\N	0.00	immediately	f	t	f	t	f	f	f	f	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	user
41abfef5-142c-456a-b854-a1e132edd830	2024-07-05 14:22:11.482597+00	Expired Package	Your parcel is going to expire in ((selected_duration)) from ((locker_number)) at ((location_name)). If you do not collect your parcel before it expires you can collect it from the front desk.	delivery	on_expired	\N	0.00	immediately	f	t	f	t	f	f	f	f	t	c6bad52f-f2b3-443d-b1e7-946d7e5b2641	\N	user
267bac75-0abc-491e-821e-aaf246f5e8c1	2024-07-05 14:22:11.482597+00	Expired Package	Your parcel is going to expire in ((selected_duration)) from ((locker_number)) at ((location_name)). If you do not collect your parcel before it expires you can collect it from the front desk.	delivery	on_expired	\N	0.00	immediately	f	t	f	t	f	f	f	f	t	b5361f54-bd98-406b-9088-ca46cab34146	\N	user
\.


--
-- Data for Name: org; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.org (id, created_at, name, active, user_pool, client_id, stripe_account_id, twilio_sid, rental_mode, storage_mode, delivery_mode, service_mode, super_tenant, id_tenant, linka_hardware, ojmar_hardware, gantner_hardware, harbor_hardware, dclock_hardware, spintly_hardware, lite_app_enabled, pending_delete, delete_issuer, pricing, product, notifications, multi_tenant, toolbox, vending_mode) FROM stdin;
fec27db7-466a-48a1-956b-cbfd7c9eb9d9	2023-07-17 00:00:01+00	demo-org	t	us-east-1_aSEeCaARi	test1	acct_1NOjpfD5DngcLH8R	\N	t	t	t	t	t	\N	t	t	t	t	t	t	t	f	\N	t	t	t	t	t	t
2a36b58a-ea63-4469-a3ba-5e6c19226689	2023-07-17 00:00:00+00	laundry-locks	f	\N	\N	acct_1NOjpfD5DngcLH8R	\N	t	t	t	t	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	t	t	t	t	t	t	t	f	\N	t	t	t	t	t	t
bc6647fb-90d8-4c79-87e9-9b6942383e4a	2023-07-17 00:00:02+00	qa-org	t	us-east-1_nWHoeULqU	6eddauveod0e8l7om47kaavc9q	acct_1NOjpfD5DngcLH8R	\N	t	t	t	t	t	\N	t	t	t	t	t	t	t	f	\N	t	t	t	t	t	t
c6bad52f-f2b3-443d-b1e7-946d7e5b2641	2024-05-30 16:38:31.113371+00	test-app	t	us-east-1_fLMbm1U7f	4o3cjhef40j40rugnt296992us	acct_1NOjpfD5DngcLH8R	\N	t	t	t	t	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	t	t	t	t	t	t	t	f	\N	t	t	t	t	t	t
b5361f54-bd98-406b-9088-ca46cab34146	2024-05-30 16:38:52.230651+00	test-invalid-data	f	us-east-1_1rm8gyLyZ	52artdg42mg074rsloogvu5eee	acct_1NOjpfD5DngcLH8R	\N	t	t	t	t	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	t	t	t	t	t	t	t	f	\N	t	t	t	t	t	t
2150d233-b4fd-4015-bb65-68d4c2d68553	2024-07-22 15:12:17.39345+00	test-org-helpdesk-verified	t	us-east-1_3FOZnzJUw	186hr47bfevhh438eba3h9vquj	\N	\N	t	t	t	t	t	bc6647fb-90d8-4c79-87e9-9b6942383e4a	t	t	t	t	t	t	t	f	\N	t	t	t	t	t	t
\.


--
-- Data for Name: org_filters; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.org_filters (id, id_org, pay_per, subscriptions, promo_codes, locations, devices, sizes, transactions, users, members, groups, issues, notifications, inventory, product_groups, conditions, reservations, reporting, subscribers) FROM stdin;
\.


--
-- Data for Name: org_settings; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.org_settings (id, id_org, default_country, default_max_reservations, default_time_zone, default_date_format, delivery_sms_start, service_sms_start, service_sms_charge, service_sms_end, event_sms_refund, invoice_prefix, default_device_hardware, default_device_mode, default_id_price, default_support_email, default_support_phone, language, default_currency, default_id_size, maintenance_on_issue, parcel_expiration, parcel_expiration_unit, use_long_parcel_codes) FROM stdin;
b61ea751-d9df-4669-9fe8-4d2966e1b425	c6bad52f-f2b3-443d-b1e7-946d7e5b2641	\N	\N	\N	\N	\N	\N	\N	\N	\N	TST	\N	\N	\N	support@koloni.me	+18337081205	en	usd	\N	t	\N	\N	\N
979be054-2beb-458c-8922-c996b49e347a	b5361f54-bd98-406b-9088-ca46cab34146	\N	\N	\N	\N	\N	\N	\N	\N	\N	TST	\N	\N	\N	support@koloni.me	+18337081205	en	usd	\N	t	\N	\N	\N
ff00a5e7-a7b0-4392-a354-d95fe112a574	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	0	string	string	string	string	string	string	string	LWH	linka	service	\N	support@koloni.me	+18337081205	en	usd	\N	f	\N	\N	\N
bdae135b-46f6-4fd5-94bd-f74e1893d221	2150d233-b4fd-4015-bb65-68d4c2d68553	\N	\N	\N	\N	\N	\N	\N	\N	\N	TST	\N	\N	\N	support@koloni.me	+18337081205	en	usd	\N	t	\N	\N	\N
\.


--
-- Data for Name: price; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.price (id, created_at, name, amount, currency, prorated, card_on_file, unit, unit_amount, price_type, id_org, "default") FROM stdin;
35a147d1-114b-46a5-8c61-46ec52c89448	2023-03-23 17:21:34.330875+00	other	3.00	aud	t	t	kg	1.00	pay_per_weight	bc6647fb-90d8-4c79-87e9-9b6942383e4a	f
510fe37c-ecc5-4fa8-acfd-77e0c4448e9a	2023-01-27 21:01:49.932443+00	free weight	0.00	usd	t	t	kg	1.00	pay_per_weight	bc6647fb-90d8-4c79-87e9-9b6942383e4a	f
c671e0ed-7e4e-46b4-96ab-b3117c148b06	2023-01-19 13:43:33.57767+00	free timer	0.00	usd	t	t	minute	1.00	pay_per_time	fec27db7-466a-48a1-956b-cbfd7c9eb9d9	f
b3e2b8e1-fa72-44c3-9222-ebd59d9b14b6	2023-05-04 19:36:16.29666+00	free time	0.00	usd	t	t	minute	1.00	pay_per_time	fec27db7-466a-48a1-956b-cbfd7c9eb9d9	f
a19f25e9-4743-4174-95bd-510e9f25edc4	2023-11-28 15:42:36.743194+00	Test	32.00	usd	t	t	hour	1.00	pay_per_time	bc6647fb-90d8-4c79-87e9-9b6942383e4a	f
18f26bc8-c006-4049-b709-b2250cb66eed	2023-11-28 15:42:46.47875+00	Test2	32.00	usd	t	t	hour	1.00	pay_per_time	bc6647fb-90d8-4c79-87e9-9b6942383e4a	f
4e7b9c5e-2e02-4f0a-89d4-9b4f6c5a9d92	2023-11-29 15:42:46.47875+00	Test2	32.00	usd	t	t	hour	1.00	pay_per_time	bc6647fb-90d8-4c79-87e9-9b6942383e4a	f
7c2b3a67-fc05-4b17-9c2f-2a23b7c9a7c7	2023-11-30 15:42:46.47875+00	weight	12.00	usd	t	t	lb	1.00	pay_per_weight	bc6647fb-90d8-4c79-87e9-9b6942383e4a	t
\.


--
-- Data for Name: product; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.product (id, created_at, image, name, description, price, sales_price, sku, msrp, serial_number, id_condition, condition, repair_on_broken, report_on_broken, id_org, id_product_group) FROM stdin;
466fad98-0b6d-4fc6-8b1e-e14d73910579	2023-10-16 17:45:45.109335+00	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/4f85710c95e14974b7bd1be6aae1bf5e.png	Test Tracking		22.00	22.00	2213ca			2fb7551c-b590-47b0-87f5-a8357f1b6f18	new	f	f	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
1ff2cb0d-a79f-4559-bfd3-e90e5c2b1d68	2024-05-17 15:21:47.924481+00	\N	Test	\N	\N	\N			\N	2fb7551c-b590-47b0-87f5-a8357f1b6f18	new	f	f	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
ae69ed01-0e9d-4a8c-8809-7cfbfa12fbfe	2024-07-05 16:26:07.62821+00	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/4f85710c95e14974b7bd1be6aae1bf5e.png	Test Tracking		\N	\N	\N	\N	\N	\N	new	f	f	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
32419cc3-dadf-4ff5-8721-c905944a8ee8	2024-07-05 16:29:17.548685+00	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/4f85710c95e14974b7bd1be6aae1bf5e.png	Test Tracking		\N	\N	\N	\N	\N	\N	new	f	f	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
\.


--
-- Data for Name: product_group; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.product_group (id, created_at, name, charging_time, one_to_one, id_org, id_size, total_inventory, transaction_number, auto_repair) FROM stdin;
dc3681ba-091b-411e-bdfc-1c1551cbc22e	2023-10-02 18:22:59.615933+00	Test	0	f	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	0	0	f
\.


--
-- Data for Name: product_tracking; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.product_tracking (id, created_at, state, id_org, id_product, id_user, id_device, id_condition) FROM stdin;
52ff5d07-15da-46bf-b7b5-9f1d2038f696	2023-10-16 17:45:47.984+00	new	bc6647fb-90d8-4c79-87e9-9b6942383e4a	466fad98-0b6d-4fc6-8b1e-e14d73910579	\N	\N	\N
4fe6a29c-88b2-49f0-9ff7-8bb34bb007b5	2023-12-11 19:32:18.269672+00	incoming	bc6647fb-90d8-4c79-87e9-9b6942383e4a	466fad98-0b6d-4fc6-8b1e-e14d73910579	c90308b9-24db-4f17-b397-d9a477f0031d	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N
fbd2c171-3be5-4a1e-b442-e51be69c5d24	2023-12-11 19:32:29.568497+00	outgoing	bc6647fb-90d8-4c79-87e9-9b6942383e4a	466fad98-0b6d-4fc6-8b1e-e14d73910579	c90308b9-24db-4f17-b397-d9a477f0031d	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N
ddba61a2-fd0f-4fa8-b504-14b87f7ba610	2023-12-11 19:32:51.749246+00	incoming	bc6647fb-90d8-4c79-87e9-9b6942383e4a	466fad98-0b6d-4fc6-8b1e-e14d73910579	\N	3b67256b-0869-4c6a-8720-391dd3d5b67d	\N
335d485b-4932-45a8-ac34-47ee45782d18	2024-05-17 15:21:49.151073+00	new	bc6647fb-90d8-4c79-87e9-9b6942383e4a	1ff2cb0d-a79f-4559-bfd3-e90e5c2b1d68	\N	\N	\N
83158198-293c-41ea-ad65-85af67f7310a	2024-06-25 19:25:36.258737+00	outgoing	bc6647fb-90d8-4c79-87e9-9b6942383e4a	1ff2cb0d-a79f-4559-bfd3-e90e5c2b1d68	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N
0a2085bb-5b95-4819-bdba-dcfef13b6b9b	2024-06-26 13:54:30.555652+00	outgoing	bc6647fb-90d8-4c79-87e9-9b6942383e4a	1ff2cb0d-a79f-4559-bfd3-e90e5c2b1d68	e8442381-7053-411c-9c43-1458ca7b18a2	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N
c3ab9a57-a1b8-4464-a270-1edd8ebfd637	2024-07-05 16:26:09.174027+00	new	bc6647fb-90d8-4c79-87e9-9b6942383e4a	ae69ed01-0e9d-4a8c-8809-7cfbfa12fbfe	\N	\N	\N
a6326b8f-df5d-4e1f-9d63-ef7a7009732a	2024-07-05 16:29:18.946921+00	new	bc6647fb-90d8-4c79-87e9-9b6942383e4a	32419cc3-dadf-4ff5-8721-c905944a8ee8	\N	\N	\N
3bebd097-81dc-4c33-8249-068576937789	2024-07-31 17:48:14.91179+00	outgoing	bc6647fb-90d8-4c79-87e9-9b6942383e4a	1ff2cb0d-a79f-4559-bfd3-e90e5c2b1d68	2c006625-1907-414d-8aca-60445d38835f	7144fcf6-ce2b-47b8-afe3-58381c2449fc	\N
\.


--
-- Data for Name: promo; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.promo (id, created_at, start_time, end_time, name, code, amount, discount_type, id_org) FROM stdin;
c671e0ed-7e4e-46b4-96ab-b3117c148b06	2023-01-19 13:43:33.57767+00	2023-05-05 14:39:53.988+00	2023-05-05 14:39:53.988+00	Test Promo	string	123.00	percentage	fec27db7-466a-48a1-956b-cbfd7c9eb9d9
7081ec4b-9913-453e-973a-7afb9e795ab5	2024-06-03 17:23:55.179328+00	2024-06-03 17:23:39.872+00	2024-06-03 17:23:39.872+00	Test Promo Code	TESTPROMO	50.00	percentage	bc6647fb-90d8-4c79-87e9-9b6942383e4a
\.


--
-- Data for Name: report; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.report (id, created_at, name, contents, id_org, version, target_org, assign_to, send_time, last_content, last_sent, recurrence, weekday, month) FROM stdin;
ff259de1-9f2b-427a-8ebd-7d1c413a42fe	2024-02-16 14:45:32.818501+00	Test223	{transactions,top_locations}	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	\N	{}	00:00	\N	\N	\N	\N	\N
d6ee8390-947b-4be2-8d02-7a1bcf0a252a	2024-02-16 14:45:38.14976+00	Test2234	{transactions,top_locations}	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	\N	{}	00:00	\N	\N	\N	\N	\N
581527fd-4789-4dcf-938e-2222cb2ab94d	2024-03-19 18:14:13.630678+00	Test	{transactions,top_locations}	bc6647fb-90d8-4c79-87e9-9b6942383e4a	report_581527fd-4789-4dcf-938e-2222cb2ab94d_1710872053	bc6647fb-90d8-4c79-87e9-9b6942383e4a	{d747fac0-e162-4f1f-a856-2f5487779331}	18:15	\N	\N	\N	\N	\N
a0fbd329-acca-4e24-b3df-ac0f105fa880	2024-04-10 18:30:28.355099+00	Test	{transactions,top_locations}	bc6647fb-90d8-4c79-87e9-9b6942383e4a	report_a0fbd329-acca-4e24-b3df-ac0f105fa880_1712773828	bc6647fb-90d8-4c79-87e9-9b6942383e4a	{931b52bf-21dd-42e3-bf28-031dca40ff21}	00:00	\N	\N	\N	\N	\N
d1a52f22-d6cf-44dc-85a0-45932884fefb	2024-04-10 18:31:46.820509+00	Test	{transactions,top_locations}	bc6647fb-90d8-4c79-87e9-9b6942383e4a	report_d1a52f22-d6cf-44dc-85a0-45932884fefb_1712773906	bc6647fb-90d8-4c79-87e9-9b6942383e4a	{931b52bf-21dd-42e3-bf28-031dca40ff21}	00:00	\N	\N	weekly	\N	\N
\.


--
-- Data for Name: reservation; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.reservation (id, created_at, start_date, end_date, recurring, sunday, monday, tuesday, wednesday, thursday, friday, saturday, from_time, to_time, id_org, id_user, id_device, id_location, id_size, id_product, mode, tracking_number) FROM stdin;
dad82540-5e6e-4b8a-93bf-e319bb07a6d7	2024-04-08 19:40:47.159936+00	2024-04-08 19:39:59.724753+00	\N	t	t	t	t	t	t	t	t	00:00	23:59	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	\N	5e27cb08-fdc8-44c7-9755-5853c3c2b5b1	8a7554f9-fabd-495b-9ec1-b6cd90ed1c85	\N	\N	\N
69675fe9-7eb6-49c3-a9ee-3b4096bc3575	2024-04-08 19:40:47.934036+00	2024-04-08 19:39:59.724753+00	\N	t	t	t	t	t	t	t	t	00:00	23:59	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	\N	5e27cb08-fdc8-44c7-9755-5853c3c2b5b1	8a7554f9-fabd-495b-9ec1-b6cd90ed1c85	\N	\N	\N
6dca114c-85be-495b-a0e4-145ede2e0e41	2024-04-08 19:40:47.968806+00	2024-04-09 16:24:54.491316+00	\N	f	t	t	t	t	t	t	t	22:08	02:28	bc6647fb-90d8-4c79-87e9-9b6942383e4a	e8442381-7053-411c-9c43-1458ca7b18a2	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: reservation_settings; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.reservation_settings (id, id_org, max_rental_time, max_rental_time_period, max_reservation_time, max_reservation_time_period, transaction_buffer_time, locker_buffer_time, transaction_buffer_time_period, locker_buffer_time_period) FROM stdin;
20afe698-1325-4f12-8d29-47269fcad862	bc6647fb-90d8-4c79-87e9-9b6942383e4a	12	minute	12	minute	12	12	\N	\N
\.


--
-- Data for Name: reservation_widget_settings; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.reservation_widget_settings (id, id_org, primary_color, secondary_color, background_color, duration, in_app_payment, duration_unit) FROM stdin;
255ca906-e1f5-4308-b926-5b0ed64f616b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	#fffff0	#ffffff	#ffffff	23	f	hour
\.


--
-- Data for Name: role; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.role (id, created_at, role, user_id, id_org, pin_code) FROM stdin;
a836db1d-816c-4682-b25d-7c7c315157ce	2023-05-11 16:22:06.726301+00	admin	049785b2-3d0c-43ee-9e39-cde07fc2ce9c	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
bc2a53a8-b6d6-48e7-a705-2799b72f1697	2023-05-11 16:22:06.858879+00	admin	0c30c524-e8e4-45ad-a8c5-20721e92a6ae	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
b93f4425-f465-4553-a585-53dcee6a10d7	2023-05-11 16:22:06.861734+00	admin	b4514995-bd60-42d9-9221-7fb9b9fa16de	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
26f62778-627e-4016-b2f1-4e6a19075911	2023-05-11 16:22:06.864128+00	admin	b707a5a9-84d4-4c46-a610-c165d94a4a11	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
2ddcddcf-4087-409e-bbf4-0f6d04db06cc	2023-05-31 17:17:42.471217+00	admin	741ac66b-1122-4222-81dc-0025f9a58a23	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
6388a598-afcb-4ceb-90ab-f64ba677d33c	2023-07-07 13:26:44.35188+00	admin	1e165a60-4acc-4bce-9cb2-14b20dd1c435	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
288220d9-50a6-4a9a-a685-24e2ea22cfbb	2023-07-07 13:26:44.452897+00	admin	3611bf41-fe11-4707-85a2-598bb1fa2762	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
18864fee-c21c-46d8-a7cf-190e8bf0fda1	2023-07-07 13:26:44.45748+00	admin	4ebfb789-5cb6-42ad-a04f-f6c20501f7c3	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
0c61bd11-95df-4607-8af8-6d2622d47bca	2023-07-07 13:26:44.46212+00	admin	9fe28767-0f89-4c53-8a5d-b24d1f82e681	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
765c2a42-c15a-424b-bde3-dbe8d8326d04	2023-11-07 15:53:00.699252+00	admin	e3dc711e-1197-4f34-aaa9-441c22953d76	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
a92c9cbc-93fa-4e81-9662-50904aeff5ab	2024-01-22 18:17:58.941644+00	admin	14728525-9979-4d09-aafc-76fef0c456d7	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
7f02ce3c-1124-4e38-9a2c-ede14524c1ae	2024-01-22 18:18:01.733382+00	admin	357d5e5a-9ed9-4a27-a1b9-9a65371f0ce8	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
0bf9bcec-dd1e-46c4-b30c-3157774284cd	2024-01-22 18:18:02.461288+00	admin	3b1ff975-4347-4eb6-a0fb-9b83a141b10e	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
234555c7-8a5c-4aa2-8e29-cb113989fbde	2024-01-22 18:18:03.192521+00	admin	4030409d-ef49-4d69-8d66-c1699b0b1e0e	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
c0fd5c67-d69d-467d-ac4b-320728c861be	2024-01-22 18:18:03.916036+00	admin	5701a381-ae70-4ec3-81d0-41d7439585e6	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
94e1eb77-a1e1-499b-856a-12b2962d7916	2024-01-22 18:18:04.642411+00	admin	5cbb55be-6f77-4731-9e83-1b269e510b9d	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
deb23e33-fa23-4fc6-9746-14ace798866a	2024-01-22 18:18:05.390261+00	admin	72e2c6a3-7e94-45d0-a3a3-22199aa57114	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
4a37e2fb-d679-4700-abcc-c25b94fb7495	2024-01-22 18:18:06.205475+00	admin	855011e1-f6e2-4345-9f62-d44d1e4d52ca	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
328b52b7-f982-4f6c-91e0-f14f09c8cf25	2024-01-22 18:18:07.018625+00	admin	911194a0-bd91-4ac9-b677-bc2be61064f6	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
2446a082-8e78-4dff-aef5-a023f0ac7643	2024-01-22 18:18:07.81447+00	admin	99d9d91d-de28-48d7-8228-5cf6d6b6404f	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
3841e496-618c-437b-8aae-f276c7bd3196	2024-01-22 18:18:08.647135+00	admin	a2f35380-24cc-482c-9ca5-8f88ab9b6933	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
13679da8-128b-4d04-80c3-e7f4ca1b382c	2024-01-22 18:18:09.417125+00	admin	a7ae3566-7cfd-4171-b479-e1250c0a7a83	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
21aa5850-f9ba-4e00-a03e-338faba6c8d1	2024-01-22 18:18:10.194414+00	admin	bd371d3c-07b8-4c4b-9602-e884a2119f31	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
98b0b125-69dd-4e19-9d8f-cb8681b2275b	2024-01-22 18:18:10.971268+00	admin	be20b071-2dad-4649-a324-27dcd45c8331	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
ef4063c8-9189-46b0-92d7-bdb0ed93672d	2024-01-22 18:18:11.747664+00	admin	ca169934-51b2-42a3-8784-2767fe4b8b94	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
e15c21bd-4386-451b-bcbe-72301da5bb30	2024-01-22 18:18:12.491925+00	admin	ce368b70-aefd-495c-bb40-529ce2d24199	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
25c57c4d-e354-4e71-b596-69f3739f62a4	2024-01-22 18:18:13.219468+00	admin	d38d7e82-be3e-4951-99b2-6a05e555b43b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
20920667-7b28-4bb6-a3cb-ab3091e6dc63	2024-01-22 18:18:13.953705+00	admin	e12a627a-bd33-4264-9cc5-b91bcd43aa39	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
3bec0acf-0bca-4530-8339-3f1675328763	2024-01-22 18:18:14.704355+00	admin	e6382379-a6e7-4423-b2df-eab873cfd3d8	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
8c5a9710-229d-4c6c-b3ed-e205c184ca53	2024-01-22 18:18:15.468793+00	admin	e962ffad-882f-4f94-90fe-9f7204c92b81	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
0a562e5c-6ee4-4844-bff7-ccf88fc5ff62	2024-01-22 18:18:16.245501+00	admin	efaa21ff-93ef-4ebb-8eaf-62e7d3dc73b3	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
c486adab-6865-43e9-a09b-2bdc3d8be345	2024-01-22 18:18:17.058219+00	admin	f7812301-955e-43ff-8857-b40c463450ee	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
808eb9d5-3c10-42c2-995e-0401040303f5	2024-02-12 16:56:42.738739+00	admin	ff4e4487-9d67-4065-8cf9-2bf6c532f2db	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
2666eec4-9170-41c0-af14-8502c0df3ac0	2024-02-12 16:56:45.340923+00	admin	a6b4d90c-b455-45f1-a79d-c5b47521bc5b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
75fa4ea8-e9c1-4323-b60d-07beb40a8a7d	2024-02-12 16:57:14.613542+00	admin	d8b16b85-33eb-495d-874b-821e54c17a34	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
21a16753-f8e6-46da-8c88-9d8e48c09dd6	2024-02-16 14:45:05.202114+00	admin	43a98c04-5a6e-47ed-a25a-59ee0a7c6eca	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
5039e291-7fb4-4b6d-864b-f334b6f15cfd	2024-03-08 14:40:48.469629+00	admin	9a4afad1-78ee-4813-ae95-7165ccc3d945	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
081377b5-6515-4d33-90e7-d05e2eec1479	2024-03-08 14:40:50.474494+00	admin	ac473ff6-7139-468a-9ff4-8ce1b417651b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
da47aa2f-d2ab-403b-94f0-afd2cecaecc2	2024-03-08 14:40:51.445677+00	admin	bb1d2210-18d8-49a5-872b-757636af1ef4	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
dcce857a-7ca3-4317-8799-be531d8ee50a	2024-03-08 14:40:52.76132+00	admin	c6bfba91-d1e5-4035-a940-a7cd57714cef	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
2531ad97-b79f-4480-bc57-55ad359b0a27	2024-03-08 14:40:53.558031+00	admin	d747fac0-e162-4f1f-a856-2f5487779331	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
eb4d9c37-d3dd-4a4e-b984-5612e89b2d7c	2024-04-09 17:47:02.26524+00	admin	931b52bf-21dd-42e3-bf28-031dca40ff21	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
b4653169-642e-42d0-b664-b7e3ea00958b	2024-04-10 18:30:08.355382+00	admin	7bfde0e2-713b-45d1-a2fe-7a64ab4b7b44	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
2d47eb65-a053-49f8-ad17-b3bb4a84a686	2024-04-25 15:13:19.994197+00	admin	df458249-15e5-4d46-ae15-b4ccba376428	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
9b1e1627-a6b6-4422-80c4-403347390ed1	2024-05-21 16:42:36.256395+00	admin	84083458-5031-70ca-61a5-ed56143f3630	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
85f95881-39f1-437e-b4ba-7a1129e487a0	2024-05-30 16:38:37.303653+00	admin	04888498-4041-7038-1bb6-f9c74f83b21d	c6bad52f-f2b3-443d-b1e7-946d7e5b2641	\N
ca6d6e06-e27f-4f03-b4c7-fb3877ca3c78	2024-05-30 16:38:57.971582+00	admin	1498c468-d011-7057-8a2e-70300fe1841f	b5361f54-bd98-406b-9088-ca46cab34146	\N
817a7193-6764-4d47-9860-cc9ad8e80b8a	2024-07-03 16:07:58.811778+00	admin	ff4e4487-9d67-4065-8cf9-2bf6c532f2db	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
c1629cbc-4128-44f6-8490-b482832471c8	2024-07-03 15:50:58.524186+00	admin	230021c8-71a0-4899-877f-8993ce9ad68b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	1235
66819b41-59a5-4628-95be-309d7ad0bb6f	2024-07-03 16:06:59.07536+00	admin	7bfde0e2-713b-45d1-a2fe-7a64ab4b7b44	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
e13fa968-f44a-4ff8-a44f-d3a6e21df5e7	2024-07-03 16:07:00.591545+00	admin	9a4afad1-78ee-4813-ae95-7165ccc3d945	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
a3b531ae-4433-4676-824f-2c6fbdce73b7	2024-07-03 16:07:01.578738+00	admin	a6b4d90c-b455-45f1-a79d-c5b47521bc5b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
745e7fd9-a4b0-4fd6-b6b3-c600dc0e9cfa	2024-07-03 16:07:02.56531+00	admin	ac473ff6-7139-468a-9ff4-8ce1b417651b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
32a1c561-ac70-41a6-8d37-386a5a24408e	2024-07-03 16:07:03.552637+00	admin	ff4e4487-9d67-4065-8cf9-2bf6c532f2db	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
14dc4e9b-90c2-4f25-925d-2e9e2c287937	2024-07-03 16:07:55.505344+00	admin	7bfde0e2-713b-45d1-a2fe-7a64ab4b7b44	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
876f239a-ba0c-441c-bfdd-7d381b240402	2024-07-03 16:07:56.345917+00	admin	9a4afad1-78ee-4813-ae95-7165ccc3d945	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
3b91b141-f2ec-4889-a3d2-30bc973cd35f	2024-07-03 16:07:57.158073+00	admin	a6b4d90c-b455-45f1-a79d-c5b47521bc5b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
868c800b-5c80-4694-a904-b1277700e7c4	2024-07-03 16:07:57.988051+00	admin	ac473ff6-7139-468a-9ff4-8ce1b417651b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
4ef59971-41d4-434c-bb2e-0b90672ac122	2024-07-03 16:08:00.552852+00	admin	7bfde0e2-713b-45d1-a2fe-7a64ab4b7b44	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
65289bc4-38dd-4ee5-86bf-ae18196d5eb2	2024-07-03 16:08:01.384517+00	admin	9a4afad1-78ee-4813-ae95-7165ccc3d945	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
b0772232-1afe-41d2-be70-909ee5786c88	2024-07-03 16:08:02.244316+00	admin	a6b4d90c-b455-45f1-a79d-c5b47521bc5b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
c306effe-a9dd-4876-a08b-ba031a174184	2024-07-03 16:08:03.142571+00	admin	ac473ff6-7139-468a-9ff4-8ce1b417651b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
91095888-50f2-4566-bca6-dd1441c41559	2024-07-03 16:08:04.067528+00	admin	ff4e4487-9d67-4065-8cf9-2bf6c532f2db	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
199efa80-ace6-43ac-b53b-83f5e8a3f6ed	2023-05-10 18:54:04.490948+00	admin	3fb773a7-1fda-41aa-a91b-8238027bc1a3	bc6647fb-90d8-4c79-87e9-9b6942383e4a	255329
cc94f801-c52b-4a0c-9016-35da2cf872cd	2024-07-03 16:08:43.015532+00	admin	7bfde0e2-713b-45d1-a2fe-7a64ab4b7b44	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
58617e42-011f-4a47-8051-ceaa1af65254	2024-07-03 16:08:43.939242+00	admin	9a4afad1-78ee-4813-ae95-7165ccc3d945	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
14811a2a-77bf-48e4-984d-7629fe5eabc5	2024-07-03 16:08:44.79299+00	admin	a6b4d90c-b455-45f1-a79d-c5b47521bc5b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
47765bb2-1029-42d6-a92d-6b032ab1ba56	2024-07-03 16:08:45.644612+00	admin	ac473ff6-7139-468a-9ff4-8ce1b417651b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
14c74ff8-b6f7-4e60-936c-c9ba145d3d85	2024-07-03 16:08:46.468493+00	admin	ff4e4487-9d67-4065-8cf9-2bf6c532f2db	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
4cc4525e-f2ff-4236-ae42-f03efc1fece8	2024-07-04 18:14:22.583563+00	admin	7bfde0e2-713b-45d1-a2fe-7a64ab4b7b44	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
7b909305-5b5d-4fdc-81d8-cbb4eb591b7b	2024-07-04 18:14:23.363882+00	admin	9a4afad1-78ee-4813-ae95-7165ccc3d945	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
59fd88b4-4f73-4880-9e71-b24eeda91d03	2024-07-04 18:14:24.119786+00	admin	a6b4d90c-b455-45f1-a79d-c5b47521bc5b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
6261cd1b-9498-4799-83d9-ca3965563a93	2024-07-04 18:14:24.843979+00	admin	ac473ff6-7139-468a-9ff4-8ce1b417651b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
aa06efcc-9d9c-48c1-aef4-0247a5b6632c	2024-07-04 18:14:25.585244+00	admin	ff4e4487-9d67-4065-8cf9-2bf6c532f2db	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
5e5b3fcd-e2b7-4626-80cb-64ecfff30243	2024-07-04 18:14:27.910101+00	admin	7bfde0e2-713b-45d1-a2fe-7a64ab4b7b44	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
c87ff97b-51d3-4ccf-999c-617b26bc6713	2024-07-04 18:14:28.740493+00	admin	9a4afad1-78ee-4813-ae95-7165ccc3d945	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
3c78b44a-8d55-428a-a53f-9f9ea5d46d24	2024-07-04 18:14:29.625272+00	admin	a6b4d90c-b455-45f1-a79d-c5b47521bc5b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
cf39fdf5-0c0e-4d4a-a692-9e70b347d988	2024-07-04 18:14:30.427041+00	admin	ac473ff6-7139-468a-9ff4-8ce1b417651b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
fdfbf352-727b-45cb-bf00-ed92886c9556	2024-07-04 18:14:31.212339+00	admin	ff4e4487-9d67-4065-8cf9-2bf6c532f2db	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
da48c8ff-a671-40cd-97ac-8e62b2991627	2024-07-04 18:14:36.611777+00	admin	7bfde0e2-713b-45d1-a2fe-7a64ab4b7b44	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
e6d3b8c6-df22-4f48-9e3b-cd4dbb445d42	2024-07-04 18:14:37.847945+00	admin	9a4afad1-78ee-4813-ae95-7165ccc3d945	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
adb84147-9c65-4917-9ab6-2bfd00d80a10	2024-07-04 18:14:38.614672+00	admin	a6b4d90c-b455-45f1-a79d-c5b47521bc5b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
604b0b3a-eca3-46ad-98cd-d1d48dcf7f70	2024-07-04 18:14:39.400871+00	admin	ac473ff6-7139-468a-9ff4-8ce1b417651b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
a74386ed-f958-413b-976b-e4ee96d0ed1f	2024-07-04 18:14:40.145607+00	admin	ff4e4487-9d67-4065-8cf9-2bf6c532f2db	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
ec1cae3f-2c80-4f61-818f-73647524c7ab	2024-07-04 18:14:53.893023+00	admin	d01a5b08-0e50-4ec3-96d8-fec5892ff659	bc6647fb-90d8-4c79-87e9-9b6942383e4a	2553
007e16c5-5d84-41c3-add2-91396ef97543	2024-07-04 18:14:55.622394+00	admin	7bfde0e2-713b-45d1-a2fe-7a64ab4b7b44	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
039891e8-414d-421c-914d-fcc96aaf7f6f	2024-07-04 18:14:56.858748+00	admin	9a4afad1-78ee-4813-ae95-7165ccc3d945	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
2e9ddadc-1dec-49b1-a241-de7032d6107c	2024-07-04 18:14:57.62289+00	admin	a6b4d90c-b455-45f1-a79d-c5b47521bc5b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
b3aa2dd4-87c7-43a8-89b7-e1a6cff7e155	2024-07-04 18:14:58.384032+00	admin	ac473ff6-7139-468a-9ff4-8ce1b417651b	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
ae8c578a-a6d1-49f4-a252-5a227745dcac	2024-07-04 18:14:59.114817+00	admin	ff4e4487-9d67-4065-8cf9-2bf6c532f2db	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N
77819a79-5e95-4eaf-b9ed-c2a0d126cf0c	2024-07-22 15:12:24.700063+00	admin	44d864d8-20b1-7039-1f20-a7cc6ddea87f	2150d233-b4fd-4015-bb65-68d4c2d68553	\N
b742a849-cfa0-4b44-a5f3-fb8167f58f8a	2024-07-22 15:13:48.534664+00	admin	54e8f4e8-1051-7088-0570-ebbc6e1bf545	2150d233-b4fd-4015-bb65-68d4c2d68553	\N
\.


--
-- Data for Name: role_permission; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.role_permission (id, role_id, permission) FROM stdin;
\.


--
-- Data for Name: size; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.size (id, created_at, name, external_id, width, depth, height, id_org, image, description) FROM stdin;
3c2d70ae-712e-4219-a159-0f5d683e5dd0	2023-01-19 13:43:56.773556+00	box size	\N	12.0000	12.0000	12.0000	fec27db7-466a-48a1-956b-cbfd7c9eb9d9	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/fceab2de675e4f87a2187e26e1f3bfa5.png	\N
b9194fd7-f22f-4afe-b6e4-ff2b770caed9	2023-05-04 19:47:27.110077+00	Laundry XL	\N	2.0000	2.0000	2.0000	fec27db7-466a-48a1-956b-cbfd7c9eb9d9	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/fceab2de675e4f87a2187e26e1f3bfa5.png	\N
feab97c9-b758-4be7-8b07-ebd6da8edfa7	2023-01-27 21:01:59.834713+00	Test	TST1	3.0000	3.0000	3.0000	bc6647fb-90d8-4c79-87e9-9b6942383e4a	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/fceab2de675e4f87a2187e26e1f3bfa5.png	\N
f7724b90-4736-4903-a205-84aa8baa4b4e	2024-02-15 15:24:49.529406+00	test	2231	1.0000	1.0000	1.0000	bc6647fb-90d8-4c79-87e9-9b6942383e4a	http://test.com	Some Description
1993cef7-0455-4e45-bfce-07a63c0cf56d	2024-02-16 14:46:09.810461+00	test	test	2.0000	3.0000	4.0000	bc6647fb-90d8-4c79-87e9-9b6942383e4a	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/fceab2de675e4f87a2187e26e1f3bfa5.png	test
d9d1c104-d99b-4de0-a969-9a4962092dc3	2024-02-16 14:48:44.861151+00	test	test232	2.0000	3.0000	4.0000	bc6647fb-90d8-4c79-87e9-9b6942383e4a	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/fceab2de675e4f87a2187e26e1f3bfa5.png	test
ae112167-4790-437d-b0e6-f97708ffda14	2024-02-16 14:48:52.539305+00	test	test2325	2.0000	3.0000	4.0000	bc6647fb-90d8-4c79-87e9-9b6942383e4a	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/fceab2de675e4f87a2187e26e1f3bfa5.png	test
5d63fccd-e542-45f2-9d10-6be026174ee0	2024-02-16 14:49:34.415139+00	test	test2326909-5	2.0000	3.0000	4.0000	bc6647fb-90d8-4c79-87e9-9b6942383e4a	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/fceab2de675e4f87a2187e26e1f3bfa5.png	test
faa9d071-f406-4d04-8040-332a1a0bb8ad	2024-02-16 14:51:46.088276+00	test2	test2326909-500	2.0000	3.0000	4.0000	bc6647fb-90d8-4c79-87e9-9b6942383e4a	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/fceab2de675e4f87a2187e26e1f3bfa5.png	test
8a7554f9-fabd-495b-9ec1-b6cd90ed1c85	2024-02-16 14:53:04.250191+00	test23	test2326909-5009	2.0000	3.0000	4.0000	bc6647fb-90d8-4c79-87e9-9b6942383e4a	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/fceab2de675e4f87a2187e26e1f3bfa5.png	test
69cfc633-59f7-4822-b706-b411ff17b04b	2024-06-10 15:15:50.280665+00	string	string	2.0000	2.0000	2.0000	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	string
\.


--
-- Data for Name: webhook; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.webhook (id, url, signature_key, status, id_org) FROM stdin;
1012ae3e-c3f8-400e-9f21-6cb534440d00	http://host.docker.internal:8000/webhook	12f2d0233eb2d89febffb92d62ed6c46b3eeeccdc5b939f4df515d59ef7f9967	ok	fec27db7-466a-48a1-956b-cbfd7c9eb9d9
a62cee3a-dcf6-4e30-b724-911f1367513a	http://localhost:3030/webhook	13352d781d0f0b3866ae9287be038e68b36ddbbb7b52038d4c995a9082635239	inactive	bc6647fb-90d8-4c79-87e9-9b6942383e4a
\.


--
-- Data for Name: white_label; Type: TABLE DATA; Schema: public; Owner: koloni
--

COPY public.white_label (id, created_at, image_key, app_logo, app_name, primary_color, secondary_color, tertiary_color, link_text_color, button_text_color, privacy_policy, user_agreement, terms_condition, organization_owner, id_org, terms_condition_2nd, terms_name_2nd) FROM stdin;
b3d33f2c-4c2a-4c8b-a2be-55bd632677a2	2024-05-30 16:38:33.475595+00	c6bad52f-f2b3-443d-b1e7-946d7e5b2641/26dff266ffc646d69dfc28355bfb7cd7.png	https://koloni-org-data.s3.amazonaws.com/c6bad52f-f2b3-443d-b1e7-946d7e5b2641/26dff266ffc646d69dfc28355bfb7cd7.png	Test app	#a2123					https://www.koloni.io/legal/privacy	https://www.koloni.io/legal/eula	https://www.koloni.io/legal/legal	julio@koloni.me	c6bad52f-f2b3-443d-b1e7-946d7e5b2641	\N	\N
ba674b1a-bd9c-45af-97f1-f708d0fef430	2024-05-30 16:38:54.258488+00	b5361f54-bd98-406b-9088-ca46cab34146/3958d58229f640318800d9162e5075e6.png	https://koloni-org-data.s3.amazonaws.com/b5361f54-bd98-406b-9088-ca46cab34146/3958d58229f640318800d9162e5075e6.png	Test invalid data	#a2123					https://www.koloni.io/legal/privacy	https://www.koloni.io/legal/eula	https://www.koloni.io/legal/legal	julio@koloni.me	b5361f54-bd98-406b-9088-ca46cab34146	\N	\N
69809a8a-0c03-4c61-957c-c78beb5ae560	2024-03-08 14:44:23.652039+00	\N	https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/3bd54df836d54c86bb7745a5998dc5d2.png	qa org	#2222	#2222	#2222	#2222	#2222	https://www.koloni.io/legal/privacy	https://www.koloni.io/legal/eula	https://www.koloni.io/legal/legal	julio@koloni.me	bc6647fb-90d8-4c79-87e9-9b6942383e4a	\N	\N
b773971c-d4e0-419d-af75-d7cdfa9b41b5	2024-07-22 15:12:20.695473+00	2150d233-b4fd-4015-bb65-68d4c2d68553/4c30067730544950b8b6c1f5a97bf33f.png	https://koloni-org-data.s3.amazonaws.com/2150d233-b4fd-4015-bb65-68d4c2d68553/4c30067730544950b8b6c1f5a97bf33f.png	Test Org Helpdesk Verified	#000000	#000000	#000000	#000000	#000000	https://www.koloni.io/legal/privacy	https://www.koloni.io/legal/eula	https://www.koloni.io/legal/legal	eduardo@koloni.me	2150d233-b4fd-4015-bb65-68d4c2d68553	\N	\N
\.


--
-- Name: User User_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public."User"
    ADD CONSTRAINT "User_pkey" PRIMARY KEY (id);


--
-- Name: User User_user_id_key; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public."User"
    ADD CONSTRAINT "User_user_id_key" UNIQUE (user_id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: api_key api_key_key_key; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT api_key_key_key UNIQUE (key);


--
-- Name: api_key api_key_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT api_key_pkey PRIMARY KEY (id);


--
-- Name: apscheduler_jobs apscheduler_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.apscheduler_jobs
    ADD CONSTRAINT apscheduler_jobs_pkey PRIMARY KEY (id);


--
-- Name: codes codes_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.codes
    ADD CONSTRAINT codes_pkey PRIMARY KEY (id);


--
-- Name: cognito_members_role_link cognito_members_role_link_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.cognito_members_role_link
    ADD CONSTRAINT cognito_members_role_link_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: condition condition_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.condition
    ADD CONSTRAINT condition_pkey PRIMARY KEY (id);


--
-- Name: device device_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_pkey PRIMARY KEY (id);


--
-- Name: event event_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.event
    ADD CONSTRAINT event_pkey PRIMARY KEY (id);


--
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (id);


--
-- Name: groups groups_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (id);


--
-- Name: harbor_events harbor_events_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.harbor_events
    ADD CONSTRAINT harbor_events_pkey PRIMARY KEY (id);


--
-- Name: issue issue_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.issue
    ADD CONSTRAINT issue_pkey PRIMARY KEY (id);


--
-- Name: link_device_price link_device_price_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_device_price
    ADD CONSTRAINT link_device_price_pkey PRIMARY KEY (id);


--
-- Name: link_groups_devices link_groups_devices_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_groups_devices
    ADD CONSTRAINT link_groups_devices_pkey PRIMARY KEY (id);


--
-- Name: link_groups_locations link_groups_locations_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_groups_locations
    ADD CONSTRAINT link_groups_locations_pkey PRIMARY KEY (id);


--
-- Name: link_groups_user link_groups_user_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_groups_user
    ADD CONSTRAINT link_groups_user_pkey PRIMARY KEY (id);


--
-- Name: link_member_location link_member_location_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_member_location
    ADD CONSTRAINT link_member_location_pkey PRIMARY KEY (id);


--
-- Name: link_membership_location link_membership_location_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_membership_location
    ADD CONSTRAINT link_membership_location_pkey PRIMARY KEY (id);


--
-- Name: link_notification_location link_notification_location_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_notification_location
    ADD CONSTRAINT link_notification_location_pkey PRIMARY KEY (id);


--
-- Name: link_org_user link_org_user_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_org_user
    ADD CONSTRAINT link_org_user_pkey PRIMARY KEY (id_org, id_user);


--
-- Name: link_user_devices link_user_devices_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_user_devices
    ADD CONSTRAINT link_user_devices_pkey PRIMARY KEY (id);


--
-- Name: link_user_locations link_user_locations_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_user_locations
    ADD CONSTRAINT link_user_locations_pkey PRIMARY KEY (id);


--
-- Name: lite_app_settings lite_app_settings_id_key; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.lite_app_settings
    ADD CONSTRAINT lite_app_settings_id_key UNIQUE (id);


--
-- Name: location location_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.location
    ADD CONSTRAINT location_pkey PRIMARY KEY (id);


--
-- Name: locker_wall locker_wall_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.locker_wall
    ADD CONSTRAINT locker_wall_pkey PRIMARY KEY (id);


--
-- Name: log log_id_key; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.log
    ADD CONSTRAINT log_id_key UNIQUE (id);


--
-- Name: memberships memberships_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.memberships
    ADD CONSTRAINT memberships_pkey PRIMARY KEY (id);


--
-- Name: notification notification_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.notification
    ADD CONSTRAINT notification_pkey PRIMARY KEY (id);


--
-- Name: org_filters org_filters_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.org_filters
    ADD CONSTRAINT org_filters_pkey PRIMARY KEY (id);


--
-- Name: org org_name_key; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.org
    ADD CONSTRAINT org_name_key UNIQUE (name);


--
-- Name: org org_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.org
    ADD CONSTRAINT org_pkey PRIMARY KEY (id);


--
-- Name: org_settings org_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.org_settings
    ADD CONSTRAINT org_settings_pkey PRIMARY KEY (id);


--
-- Name: report pk_report; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.report
    ADD CONSTRAINT pk_report PRIMARY KEY (id);


--
-- Name: price price_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.price
    ADD CONSTRAINT price_pkey PRIMARY KEY (id);


--
-- Name: product_group product_group_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.product_group
    ADD CONSTRAINT product_group_pkey PRIMARY KEY (id);


--
-- Name: product product_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_pkey PRIMARY KEY (id);


--
-- Name: product_tracking product_tracking_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.product_tracking
    ADD CONSTRAINT product_tracking_pkey PRIMARY KEY (id);


--
-- Name: promo promo_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.promo
    ADD CONSTRAINT promo_pkey PRIMARY KEY (id);


--
-- Name: reservation reservation_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.reservation
    ADD CONSTRAINT reservation_pkey PRIMARY KEY (id);


--
-- Name: reservation_widget_settings reservation_settings_id_key; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.reservation_widget_settings
    ADD CONSTRAINT reservation_settings_id_key UNIQUE (id);


--
-- Name: reservation_settings reservation_settings_id_key1; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.reservation_settings
    ADD CONSTRAINT reservation_settings_id_key1 UNIQUE (id);


--
-- Name: role_permission role_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.role_permission
    ADD CONSTRAINT role_permission_pkey PRIMARY KEY (id);


--
-- Name: role role_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.role
    ADD CONSTRAINT role_pkey PRIMARY KEY (id);


--
-- Name: size size_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.size
    ADD CONSTRAINT size_pkey PRIMARY KEY (id);


--
-- Name: webhook webhook_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.webhook
    ADD CONSTRAINT webhook_pkey PRIMARY KEY (id);


--
-- Name: white_label white_label_pkey; Type: CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.white_label
    ADD CONSTRAINT white_label_pkey PRIMARY KEY (id);


--
-- Name: ix_apscheduler_jobs_next_run_time; Type: INDEX; Schema: public; Owner: koloni
--

CREATE INDEX ix_apscheduler_jobs_next_run_time ON public.apscheduler_jobs USING btree (next_run_time);


--
-- Name: api_key api_key_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT api_key_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: codes codes_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.codes
    ADD CONSTRAINT codes_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: codes codes_id_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.codes
    ADD CONSTRAINT codes_id_user_fkey FOREIGN KEY (id_user) REFERENCES public."User"(id);


--
-- Name: cognito_members_role_link cognito_members_role_link_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.cognito_members_role_link
    ADD CONSTRAINT cognito_members_role_link_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.role(id);


--
-- Name: condition condition_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.condition
    ADD CONSTRAINT condition_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: device device_id_condition_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_id_condition_fkey FOREIGN KEY (id_condition) REFERENCES public.condition(id);


--
-- Name: device device_id_location_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_id_location_fkey FOREIGN KEY (id_location) REFERENCES public.location(id);


--
-- Name: device device_id_locker_wall_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_id_locker_wall_fkey FOREIGN KEY (id_locker_wall) REFERENCES public.locker_wall(id);


--
-- Name: device device_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: device device_id_price_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_id_price_fkey FOREIGN KEY (id_price) REFERENCES public.price(id);


--
-- Name: device device_id_product_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_id_product_fkey FOREIGN KEY (id_product) REFERENCES public.product(id);


--
-- Name: device device_id_size_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_id_size_fkey FOREIGN KEY (id_size) REFERENCES public.size(id);


--
-- Name: event event_id_device_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.event
    ADD CONSTRAINT event_id_device_fkey FOREIGN KEY (id_device) REFERENCES public.device(id);


--
-- Name: event event_id_membership_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.event
    ADD CONSTRAINT event_id_membership_fkey FOREIGN KEY (id_membership) REFERENCES public.memberships(id);


--
-- Name: event event_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.event
    ADD CONSTRAINT event_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: event event_id_promo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.event
    ADD CONSTRAINT event_id_promo_fkey FOREIGN KEY (id_promo) REFERENCES public.promo(id);


--
-- Name: event event_id_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.event
    ADD CONSTRAINT event_id_user_fkey FOREIGN KEY (id_user) REFERENCES public."User"(id);


--
-- Name: feedback feedback_id_device_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_id_device_fkey FOREIGN KEY (id_device) REFERENCES public.device(id);


--
-- Name: feedback feedback_id_location_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_id_location_fkey FOREIGN KEY (id_location) REFERENCES public.location(id);


--
-- Name: feedback feedback_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: report fk_org_target_org; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.report
    ADD CONSTRAINT fk_org_target_org FOREIGN KEY (target_org) REFERENCES public.org(id);


--
-- Name: product_tracking fk_product_tracking_condition; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.product_tracking
    ADD CONSTRAINT fk_product_tracking_condition FOREIGN KEY (id_condition) REFERENCES public.condition(id);


--
-- Name: report fk_report_id_org; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.report
    ADD CONSTRAINT fk_report_id_org FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: groups groups_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: issue issue_id_event_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.issue
    ADD CONSTRAINT issue_id_event_fkey FOREIGN KEY (id_event) REFERENCES public.event(id);


--
-- Name: issue issue_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.issue
    ADD CONSTRAINT issue_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: issue issue_id_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.issue
    ADD CONSTRAINT issue_id_user_fkey FOREIGN KEY (id_user) REFERENCES public."User"(id);


--
-- Name: link_device_price link_device_price_id_device_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_device_price
    ADD CONSTRAINT link_device_price_id_device_fkey FOREIGN KEY (id_device) REFERENCES public.device(id);


--
-- Name: link_device_price link_device_price_id_price_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_device_price
    ADD CONSTRAINT link_device_price_id_price_fkey FOREIGN KEY (id_price) REFERENCES public.price(id);


--
-- Name: link_groups_devices link_groups_devices_id_device_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_groups_devices
    ADD CONSTRAINT link_groups_devices_id_device_fkey FOREIGN KEY (id_device) REFERENCES public.device(id);


--
-- Name: link_groups_devices link_groups_devices_id_group_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_groups_devices
    ADD CONSTRAINT link_groups_devices_id_group_fkey FOREIGN KEY (id_group) REFERENCES public.groups(id);


--
-- Name: link_groups_locations link_groups_locations_id_group_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_groups_locations
    ADD CONSTRAINT link_groups_locations_id_group_fkey FOREIGN KEY (id_group) REFERENCES public.groups(id);


--
-- Name: link_groups_locations link_groups_locations_id_location_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_groups_locations
    ADD CONSTRAINT link_groups_locations_id_location_fkey FOREIGN KEY (id_location) REFERENCES public.location(id);


--
-- Name: link_groups_user link_groups_user_id_group_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_groups_user
    ADD CONSTRAINT link_groups_user_id_group_fkey FOREIGN KEY (id_group) REFERENCES public.groups(id);


--
-- Name: link_groups_user link_groups_user_id_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_groups_user
    ADD CONSTRAINT link_groups_user_id_user_fkey FOREIGN KEY (id_user) REFERENCES public."User"(id);


--
-- Name: link_member_location link_member_location_id_location_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_member_location
    ADD CONSTRAINT link_member_location_id_location_fkey FOREIGN KEY (id_location) REFERENCES public.location(id);


--
-- Name: link_membership_location link_membership_location_id_location_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_membership_location
    ADD CONSTRAINT link_membership_location_id_location_fkey FOREIGN KEY (id_location) REFERENCES public.location(id);


--
-- Name: link_membership_location link_membership_location_id_membership_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_membership_location
    ADD CONSTRAINT link_membership_location_id_membership_fkey FOREIGN KEY (id_membership) REFERENCES public.memberships(id);


--
-- Name: link_notification_location link_notification_location_id_location_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_notification_location
    ADD CONSTRAINT link_notification_location_id_location_fkey FOREIGN KEY (id_location) REFERENCES public.location(id);


--
-- Name: link_notification_location link_notification_location_id_notification_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_notification_location
    ADD CONSTRAINT link_notification_location_id_notification_fkey FOREIGN KEY (id_notification) REFERENCES public.notification(id);


--
-- Name: link_org_user link_org_user_id_favorite_location_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_org_user
    ADD CONSTRAINT link_org_user_id_favorite_location_fkey FOREIGN KEY (id_favorite_location) REFERENCES public.location(id);


--
-- Name: link_org_user link_org_user_id_membership_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_org_user
    ADD CONSTRAINT link_org_user_id_membership_fkey FOREIGN KEY (id_membership) REFERENCES public.memberships(id);


--
-- Name: link_org_user link_org_user_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_org_user
    ADD CONSTRAINT link_org_user_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: link_org_user link_org_user_id_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_org_user
    ADD CONSTRAINT link_org_user_id_user_fkey FOREIGN KEY (id_user) REFERENCES public."User"(id);


--
-- Name: link_user_devices link_user_devices_id_device_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_user_devices
    ADD CONSTRAINT link_user_devices_id_device_fkey FOREIGN KEY (id_device) REFERENCES public.device(id);


--
-- Name: link_user_devices link_user_devices_id_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_user_devices
    ADD CONSTRAINT link_user_devices_id_user_fkey FOREIGN KEY (id_user) REFERENCES public."User"(id);


--
-- Name: link_user_locations link_user_locations_id_location_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_user_locations
    ADD CONSTRAINT link_user_locations_id_location_fkey FOREIGN KEY (id_location) REFERENCES public.location(id);


--
-- Name: link_user_locations link_user_locations_id_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.link_user_locations
    ADD CONSTRAINT link_user_locations_id_user_fkey FOREIGN KEY (id_user) REFERENCES public."User"(id);


--
-- Name: lite_app_settings lite_app_settings_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.lite_app_settings
    ADD CONSTRAINT lite_app_settings_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: location location_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.location
    ADD CONSTRAINT location_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: location location_id_price_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.location
    ADD CONSTRAINT location_id_price_fkey FOREIGN KEY (id_price) REFERENCES public.price(id);


--
-- Name: locker_wall locker_wall_id_location_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.locker_wall
    ADD CONSTRAINT locker_wall_id_location_fkey FOREIGN KEY (id_location) REFERENCES public.location(id);


--
-- Name: locker_wall locker_wall_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.locker_wall
    ADD CONSTRAINT locker_wall_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: log log_id_device_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.log
    ADD CONSTRAINT log_id_device_fkey FOREIGN KEY (id_device) REFERENCES public.device(id);


--
-- Name: log log_id_event_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.log
    ADD CONSTRAINT log_id_event_fkey FOREIGN KEY (id_event) REFERENCES public.event(id);


--
-- Name: log log_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.log
    ADD CONSTRAINT log_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: memberships memberships_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.memberships
    ADD CONSTRAINT memberships_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: notification notification_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.notification
    ADD CONSTRAINT notification_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: org_filters org_filters_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.org_filters
    ADD CONSTRAINT org_filters_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: org org_id_tenant_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.org
    ADD CONSTRAINT org_id_tenant_fkey FOREIGN KEY (id_tenant) REFERENCES public.org(id);


--
-- Name: org_settings org_settings_default_id_price_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.org_settings
    ADD CONSTRAINT org_settings_default_id_price_fkey FOREIGN KEY (default_id_price) REFERENCES public.price(id);


--
-- Name: org_settings org_settings_default_id_size_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.org_settings
    ADD CONSTRAINT org_settings_default_id_size_fkey FOREIGN KEY (default_id_size) REFERENCES public.size(id);


--
-- Name: org_settings org_settings_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.org_settings
    ADD CONSTRAINT org_settings_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: price price_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.price
    ADD CONSTRAINT price_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: product_group product_group_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.product_group
    ADD CONSTRAINT product_group_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: product_group product_group_id_size_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.product_group
    ADD CONSTRAINT product_group_id_size_fkey FOREIGN KEY (id_size) REFERENCES public.size(id);


--
-- Name: product product_id_condition_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_id_condition_fkey FOREIGN KEY (id_condition) REFERENCES public.condition(id);


--
-- Name: product product_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: product product_id_product_group_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_id_product_group_fkey FOREIGN KEY (id_product_group) REFERENCES public.product_group(id);


--
-- Name: product_tracking product_tracking_id_device_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.product_tracking
    ADD CONSTRAINT product_tracking_id_device_fkey FOREIGN KEY (id_device) REFERENCES public.device(id);


--
-- Name: product_tracking product_tracking_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.product_tracking
    ADD CONSTRAINT product_tracking_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: product_tracking product_tracking_id_product_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.product_tracking
    ADD CONSTRAINT product_tracking_id_product_fkey FOREIGN KEY (id_product) REFERENCES public.product(id);


--
-- Name: product_tracking product_tracking_id_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.product_tracking
    ADD CONSTRAINT product_tracking_id_user_fkey FOREIGN KEY (id_user) REFERENCES public."User"(id);


--
-- Name: promo promo_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.promo
    ADD CONSTRAINT promo_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: reservation reservation_id_device_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.reservation
    ADD CONSTRAINT reservation_id_device_fkey FOREIGN KEY (id_device) REFERENCES public.device(id);


--
-- Name: reservation reservation_id_location_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.reservation
    ADD CONSTRAINT reservation_id_location_fkey FOREIGN KEY (id_location) REFERENCES public.location(id);


--
-- Name: reservation reservation_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.reservation
    ADD CONSTRAINT reservation_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: reservation reservation_id_product_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.reservation
    ADD CONSTRAINT reservation_id_product_fkey FOREIGN KEY (id_product) REFERENCES public.product(id);


--
-- Name: reservation reservation_id_size_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.reservation
    ADD CONSTRAINT reservation_id_size_fkey FOREIGN KEY (id_size) REFERENCES public.size(id);


--
-- Name: reservation reservation_id_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.reservation
    ADD CONSTRAINT reservation_id_user_fkey FOREIGN KEY (id_user) REFERENCES public."User"(id);


--
-- Name: reservation_widget_settings reservation_settings_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.reservation_widget_settings
    ADD CONSTRAINT reservation_settings_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: reservation_settings reservation_settings_id_org_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.reservation_settings
    ADD CONSTRAINT reservation_settings_id_org_fkey1 FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: role role_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.role
    ADD CONSTRAINT role_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: role_permission role_permission_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.role_permission
    ADD CONSTRAINT role_permission_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.role(id);


--
-- Name: size size_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.size
    ADD CONSTRAINT size_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: webhook webhook_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.webhook
    ADD CONSTRAINT webhook_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- Name: white_label white_label_id_org_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koloni
--

ALTER TABLE ONLY public.white_label
    ADD CONSTRAINT white_label_id_org_fkey FOREIGN KEY (id_org) REFERENCES public.org(id);


--
-- PostgreSQL database dump complete
--

