from datetime import timedelta

from NEMO.models import Chemical, ChemicalHazard, User
from NEMO.utilities import EmailCategory, render_email_template, send_mail
from NEMO.views.customization import get_media_file_contents
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from NEMO_user_chemicals.customizations import ChemicalsCustomization
from NEMO_user_chemicals.forms import (
    ChemicalForm,
    ChemicalRequestApprovalForm,
    ChemicalRequestForm,
    ChemicalUpdateRequestForm,
    UserChemicalForm,
)
from NEMO_user_chemicals.models import ChemicalLocation, ChemicalRequest, UserChemical
from django.utils.safestring import mark_safe


def send_new_chemical_request_email(chemical_request, request, is_edit=False):
    message = get_media_file_contents("chemical_request_email.html")
    chem_request_emails = ChemicalsCustomization.get("chemical_request_email_addresses")
    if message and chem_request_emails:
        dictionary = {
            "request": chemical_request,
            "url": request.build_absolute_uri(reverse("view_requests")),
            "request_edited": is_edit,
        }
        subject_prefix = "Updated" if is_edit else "New"
        subject = f"{subject_prefix} chemical request from {chemical_request.requester.get_full_name()}"
        content = render_email_template(message, dictionary)
        recipients = tuple([e for e in chem_request_emails.split(",") if e])
        send_mail(
            subject=subject,
            content=content,
            to=recipients,
            from_email=chemical_request.requester.email,
            email_category=EmailCategory.SAFETY,
        )


def send_chemical_request_email_update(chemical_request):
    message = get_media_file_contents("chemical_request_update_email.html")
    chem_request_emails = ChemicalsCustomization.get("chemical_request_email_addresses")
    if message and chem_request_emails:
        subject = f"Update to your Material Request for {chemical_request.name}"
        message = render_email_template(message, {"request": chemical_request})
        recipients = tuple([e for e in chem_request_emails.split(",") if e])
        send_mail(
            subject=subject,
            content=message,
            from_email=chemical_request.approver.email,
            to=[chemical_request.requester.email],
            cc=recipients,
            email_category=EmailCategory.SAFETY,
        )


@login_required
@require_GET
def dashboard(request):
    return render(request, "NEMO_user_chemicals/dashboard.html")


@login_required
@require_http_methods(["GET", "POST"])
def chemical_request(request, request_id=None):
    hazards = ChemicalHazard.objects.all()

    # Check if we are editing an existing request
    chem_req = None
    if request_id:
        chem_req = get_object_or_404(ChemicalRequest, id=request_id)
        # Only allow staff or the original requester to edit
        if not request.user.is_staff and chem_req.requester != request.user:
            return HttpResponseForbidden("You do not have permission to edit this request.")

    if request.method == "POST":
        # Pass instance=chem_req to update the existing record
        form = ChemicalRequestForm(request.user, data=request.POST, files=request.FILES, instance=chem_req)
        if form.is_valid():
            req = form.save(commit=False)

            is_edit = False
            # If editing, reset status to Pending so it gets reviewed again
            if request_id:
                req.approved = ChemicalRequest.Approval.PENDING
                is_edit = True

            req.save()
            form.save_m2m()  # Essential when using commit=False

            # Send email with edit flag using original logic
            send_new_chemical_request_email(req, request, is_edit)

            dictionary = {
                "title": "Request received",
                "heading": "Your request has been received and will be reviewed shortly.",
                "content": mark_safe(
                    f"You can view the status of your request on the <a href='{reverse('view_requests')}'>Material Requests</a> page."
                ),
            }
            return render(request, "acknowledgement.html", dictionary)
        else:
            dictionary = {"hazards": hazards, "form": form, "chemical_request": chem_req}
            return render(request, "NEMO_user_chemicals/chemical_request.html", dictionary)

    # GET Request
    dictionary = {"hazards": hazards}
    if chem_req:
        dictionary["chemical_request"] = chem_req
        # Initialize form with instance data
        form = ChemicalRequestForm(request.user, instance=chem_req)
        dictionary["form"] = form
    else:
        dictionary["form"] = ChemicalRequestForm(request.user)

    return render(request, "NEMO_user_chemicals/chemical_request.html", dictionary)


@login_required
@require_GET
def view_requests(request, sort_by="date"):
    if request.user.is_staff:
        pending_requests = ChemicalRequest.objects.filter(approved=ChemicalRequest.Approval.PENDING)
        all_requests = ChemicalRequest.objects.all()
    else:
        pending_requests = ChemicalRequest.objects.filter(
            requester=request.user, approved=ChemicalRequest.Approval.PENDING
        )
        all_requests = ChemicalRequest.objects.filter(requester=request.user)
    if sort_by == "requester":
        pending_requests = pending_requests.order_by("requester__first_name")
        all_requests = all_requests.order_by("requester__first_name")
    elif sort_by == "name":
        pending_requests = pending_requests.order_by("name")
        all_requests = all_requests.order_by("name")
    elif sort_by == "approved":
        all_requests = all_requests.order_by("approved")
    else:
        pending_requests = pending_requests.order_by("-date")
        all_requests = all_requests.order_by("-date")

    dictionary = {"pending_requests": pending_requests, "all_requests": all_requests}
    return render(request, "NEMO_user_chemicals/view_requests.html", dictionary)


@login_required
@require_GET
def request_details(request, request_id):
    req = get_object_or_404(ChemicalRequest, id=request_id)
    if not request.user.is_staff and req.requester != request.user:
        return HttpResponseRedirect(reverse("view_requests"))

    dictionary = {"chemical_request": req, "hazards": req.hazards.all()}

    # Check if this is an AJAX request using header OR explicit GET param
    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("ajax"):
        dictionary["base_template"] = "NEMO_user_chemicals/ajax_base.html"
    else:
        dictionary["base_template"] = "base.html"

    return render(request, "NEMO_user_chemicals/request_details.html", dictionary)


@staff_member_required(login_url=None)
@require_POST
def update_request(request, request_id):
    req = get_object_or_404(ChemicalRequest, id=request_id)
    form = ChemicalRequestApprovalForm(request.user, request.POST, instance=req)
    if form.is_valid():
        form.save()
        send_chemical_request_email_update(req)
        dictionary = {
            "title": "Request Status Updated",
            "heading": "You successfully updated the status of this request",
        }
        return render(request, "acknowledgement.html", dictionary)
    dictionary = {
        "title": "Request Status Update Failed",
        "heading": "There was a problem with this update.",
    }
    return render(request, "acknowledgement.html", dictionary)


@login_required
@require_GET
def user_chemicals(request, sort_by="chemical"):
    if request.user.is_staff:
        user_chems = UserChemical.objects.all()
    else:
        user_chems = UserChemical.objects.filter(owner=request.user)

    if sort_by == "owner":
        user_chems = user_chems.order_by("owner__first_name")
    elif sort_by == "chemical":
        user_chems = user_chems.order_by("chemical__name")
    elif sort_by == "label_id":
        user_chems = user_chems.order_by("label_id")
    elif sort_by == "expiration":
        user_chems = user_chems.order_by("expiration")
    elif sort_by == "location":
        user_chems = user_chems.order_by("location__name")
    else:
        user_chems = user_chems.order_by("-in_date")

    dictionary = {"user_chemicals": user_chems}
    return render(request, "NEMO_user_chemicals/user_chemicals.html", dictionary)


@login_required
@require_GET
def my_chemicals(request, sort_by="chemical"):
    user_chems = UserChemical.objects.filter(owner=request.user)

    if sort_by == "owner":
        user_chems = user_chems.order_by("owner__first_name")
    elif sort_by == "chemical":
        user_chems = user_chems.order_by("chemical__name")
    elif sort_by == "label_id":
        user_chems = user_chems.order_by("label_id")
    elif sort_by == "expiration":
        user_chems = user_chems.order_by("expiration")
    elif sort_by == "location":
        user_chems = user_chems.order_by("location__name")
    else:
        user_chems = user_chems.order_by("-in_date")

    dictionary = {"user_chemicals": user_chems, "view_name": "my_chemicals", "page_title": "My Chemicals"}
    return render(request, "NEMO_user_chemicals/user_chemicals.html", dictionary)


@staff_member_required(login_url=None)
@require_http_methods(["GET", "POST"])
def add_user_chemical(request, chem_req=None):
    if request.method == "GET":
        chem_request = get_object_or_404(ChemicalRequest, id=chem_req) if chem_req else None
        dictionary = {
            "one_year_from_now": timezone.now() + timedelta(days=365),
            "today": timezone.localdate(),
            "users": User.objects.filter(is_active=True),
            "chemicals": Chemical.objects.all(),
            "chemical_request": chem_request,
            "locations": ChemicalLocation.objects.all(),
        }
        return render(request, "NEMO_user_chemicals/add_user_chemical.html", dictionary)
    elif request.method == "POST":
        form = UserChemicalForm(data=request.POST)
        if form.is_valid() and not form.cleaned_data.get("chemical"):
            form.add_error("chemical", "You must select a valid chemical from the list.")
        if not form.is_valid():
            dictionary = {
                "title": "Chemical request failed",
                "heading": "Invalid form data",
                "content": str(form.errors),
            }
            return render(request, "acknowledgement.html", dictionary)

        user_chem = form.save(commit=False)
        # Fetch comments from cleaned_data, or fallback to request.POST
        comments = form.cleaned_data.get("comments") or request.POST.get("comments", "")
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        history_entry = f"[{timestamp}] Added: Owner: {user_chem.owner.get_full_name()}, Label ID: {user_chem.label_id}, Date In: {user_chem.in_date}, Expiration: {user_chem.expiration}. Comments: {comments}\n"
        user_chem.history = (user_chem.history or "") + history_entry
        user_chem.save()
        return HttpResponseRedirect(reverse("user_chemicals"))


@staff_member_required(login_url=None)
@require_http_methods(["GET", "POST"])
def update_user_chemical(request, chem_id):
    user_chem = get_object_or_404(UserChemical, id=chem_id)
    if request.method == "GET":
        form = UserChemicalForm(instance=user_chem)
        owner = user_chem.owner
        dictionary = {
            "form": form,
            "one_year_from_now": timezone.now() + timedelta(days=365),
            "users": User.objects.filter(is_active=True),
            "owner": owner,
            # Added chemicals to context for typeahead
            "chemicals": Chemical.objects.all(),
            "locations": ChemicalLocation.objects.all(),
        }
        return render(request, "NEMO_user_chemicals/update_user_chemical.html", dictionary)
    elif request.method == "POST":
        user_chem = get_object_or_404(UserChemical, id=chem_id)
        form = UserChemicalForm(data=request.POST, instance=user_chem)
        if form.is_valid() and not form.cleaned_data.get("chemical"):
            form.add_error("chemical", "You must select a valid chemical from the list.")
        if not form.is_valid():
            dictionary = {
                "title": "Chemical request update failed",
                "heading": "Invalid form data",
                "content": str(form.errors),
            }
            return render(request, "acknowledgement.html", dictionary)

        user_chem = form.save(commit=False)
        # Fetch comments from cleaned_data, or fallback to request.POST
        comments = form.cleaned_data.get("comments") or request.POST.get("comments", "")
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        history_entry = f"[{timestamp}] Updated: Owner: {user_chem.owner.get_full_name()}, Label ID: {user_chem.label_id}, Date In: {user_chem.in_date}, Expiration: {user_chem.expiration}. Comments: {comments}\n"
        user_chem.history = (user_chem.history or "") + history_entry
        user_chem.save()
        return HttpResponseRedirect(reverse("user_chemicals"))


@login_required
@require_http_methods(["GET", "POST"])
def request_chemical_update(request, chem_id):
    user_chem = get_object_or_404(UserChemical, id=chem_id)
    # Only allow the owner or staff to request an update
    if not request.user.is_staff and user_chem.owner != request.user:
        return HttpResponseForbidden("You do not have permission to modify this chemical.")

    if request.method == "POST":
        form = ChemicalUpdateRequestForm(request.POST)
        if form.is_valid():
            # Email logic
            chem_request_emails = ChemicalsCustomization.get("chemical_request_email_addresses")
            if chem_request_emails:
                recipients = tuple([e for e in chem_request_emails.split(",") if e])

                if recipients:
                    details = ""
                    selected_actions_display = []

                    if form.cleaned_data.get("new_owner"):
                        details += f"- New Owner: {form.cleaned_data['new_owner']}\n"
                        selected_actions_display.append("Change Owner")
                    if form.cleaned_data.get("new_location"):
                        details += f"- New Location: {form.cleaned_data['new_location']}\n"
                        selected_actions_display.append("Change Location")
                    if form.cleaned_data.get("new_bottle"):
                        selected_actions_display.append("Bring in New Bottle")
                    if form.cleaned_data.get("new_expiration"):
                        details += f"- New Expiration: {form.cleaned_data['new_expiration']}\n"
                        selected_actions_display.append("Adjust Expiration")
                    if form.cleaned_data.get("remove"):
                        selected_actions_display.append("Remove/Dispose Chemical")
                    if form.cleaned_data.get("other_comments"):
                        details += f"- Other Details: {form.cleaned_data['other_comments']}\n"
                        selected_actions_display.append("Other")

                    # Check if anything was actually requested
                    if not selected_actions_display:
                        form.add_error(None, "Please select at least one action or fill in a field.")
                        return render(
                            request, "NEMO_user_chemicals/request_update.html", {"form": form, "user_chem": user_chem}
                        )

                    subject = f"Chemical Update Request: {user_chem.chemical.name} (ID: {user_chem.label_id})"
                    content = (
                        f"User {request.user.get_full_name()} has requested an update for the following chemical:\n\n"
                        f"Chemical: {user_chem.chemical.name}\n"
                        f"Label ID: {user_chem.label_id}\n"
                        f"Current Location: {user_chem.location}\n\n"
                        f"Requested Actions: {', '.join(selected_actions_display)}\n\n"
                        f"Details:\n{details}"
                    )

                    send_mail(
                        subject=subject,
                        content=content,
                        to=recipients,
                        from_email=request.user.email,
                        email_category=EmailCategory.SAFETY,
                    )

                    dictionary = {
                        "title": "Update Request Sent",
                        "heading": "Your update request has been sent to staff.",
                        "content": mark_safe(
                            f"You will be contacted if further information is needed. Return to <a href='{reverse('my_chemicals')}'>My Chemicals</a>."
                        ),
                    }
                    return render(request, "acknowledgement.html", dictionary)
            dictionary = {
                "title": "Update Request Problem",
                "heading": "There was a problem submitting your update request. Please contact staff",
                "content": mark_safe(f"Return to <a href='{reverse('my_chemicals')}'>My Chemicals</a>."),
            }
            return render(request, "acknowledgement.html", dictionary)
    else:
        form = ChemicalUpdateRequestForm()

    return render(request, "NEMO_user_chemicals/request_update.html", {"form": form, "user_chem": user_chem})


@staff_member_required(login_url=None)
@require_POST
def delete_user_chemical(request, chem_id):
    user_chem = get_object_or_404(UserChemical, id=chem_id)
    user_chem.delete()
    return HttpResponseRedirect(reverse("user_chemicals"))


@staff_member_required(login_url=None)
@require_http_methods(["GET", "POST"])
def add_chemical(request, request_id=None):
    chem_req = None
    if request_id:
        chem_req = get_object_or_404(ChemicalRequest, id=request_id)

    if request.method == "POST":
        form = ChemicalForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            chemical = form.save(commit=False)
            # If no document uploaded but we have a request with an SDS, copy it
            if not chemical.document and chem_req and chem_req.sds:
                chemical.document.save(chem_req.sds.name, chem_req.sds)
            chemical.save()
            form.save_m2m()
            return redirect("user_chemicals_dashboard")
    else:
        initial_data = {}
        if chem_req:
            initial_data["name"] = chem_req.name
            # Use values_list to get IDs so they match the form choices in the template
            initial_data["hazards"] = chem_req.hazards.values_list("id", flat=True)

        form = ChemicalForm(initial=initial_data)

    return render(request, "NEMO_user_chemicals/add_chemical.html", {"form": form, "source_request": chem_req})
