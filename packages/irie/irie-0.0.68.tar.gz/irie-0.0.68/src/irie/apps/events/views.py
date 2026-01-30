
import os
from django.template import loader
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from irie.apps.events.models import EventRecord, HazardEvent
from .filters import EventFilter
from irie.maps import EventMap

def _filter_event_table(request):
    # Copy the GET parameters and remove the 'page' parameter
    page_query = request.GET.copy()
    page_query.pop('page', None)

    filter_set = EventFilter(request.GET, queryset=HazardEvent.objects.all())
    order_query = page_query.copy()
    if order := order_query.pop("order", None):
        try:
            events = filter_set.qs.order_by(order[0])
        except:
            if hasattr(HazardEvent, order[0]):
                events = sorted(filter_set.qs, 
                                key=lambda x: getattr(x, order[0]), reverse=True)
            elif "event_count" == order[0]:
                events = sorted(filter_set.qs, 
                                key=lambda x: x.records.count(), reverse=True)
            else:
                events = filter_set.qs
    else:
        events = filter_set.qs
    return events, (order_query, page_query, filter_set)

def _page_from_query(request)->int:
    """
    Extracts the page number from a query dictionary.
    """
    page = request.GET.get("page", 1)
    try:
        return int(page)
    except ValueError:
        return 1


# @login_required(login_url="/login/")
def asset_table(request):
    """
    Returns a table of all assets in the database, paginated
    """

    context = {
        "segment": "event",
    }

    events, (order_query, page_query, filter_set) = _filter_event_table(request)
    page = _page_from_query(request)

    context["page_query"] = page_query.urlencode()
    context["order_query"] = order_query.urlencode()
    context["events"]   = Paginator(events, 5).get_page(page)
    context["asset_map"] = EventMap(events=events).get_html()
    context["filter"] = filter_set


    html_template = loader.get_template("events/asset-table.html")
    try:
        return HttpResponse(html_template.render(context, request))

    except Exception as e:
        if "DEBUG" in os.environ and os.environ["DEBUG"]:
            raise e
        html_template = loader.get_template("site/page-500.html")
        return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def event_table(request):
    """
    This view generates the event table page.
    """
    context = {}
    page_template = "events-home.html"
    context["segment"] = "events"

    page = request.GET.get("page", 1)
    try:
        page = int(page)
    except:
        page = 1

    events = [i for i in sorted(HazardEvent.objects.all(), reverse=True)]

    paginator = Paginator(events, 20)

    context["events"] = paginator.get_page(page)


    html_template = loader.get_template("events/" + page_template)

    try:
        return HttpResponse(html_template.render(context, request))

    except Exception as e:
        if "DEBUG" in os.environ and os.environ["DEBUG"]:
            raise e
        html_template = loader.get_template("site/page-500.html")
        return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def event_summary(request, anssid):
    """
    This view generates the event summary page.
    """
    context = {}
    page_template = "event-profile.html"
    context["segment"] = "events"

    try:
        event = HazardEvent.objects.get(usgsid=anssid)
    except HazardEvent.DoesNotExist:
        event = None

    context["event"] = event

    html_template = loader.get_template("events/" + page_template)

    try:
        return HttpResponse(html_template.render(context, request))

    except Exception as e:
        if "DEBUG" in os.environ and os.environ["DEBUG"]:
            raise e
        html_template = loader.get_template("site/page-500.html")
        return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def record_table(request):
    """
    This view generates the event table page. 
    It uses event-table.html
    """
    context = {}
    page_template = "event-table.html"
    context["segment"] = "events"

    page = request.GET.get("page", 1)
    try:
        page = int(page)
    except:
        page = 1

    asset = request.GET.get("asset", None)

    if asset is not None:
        events = [i for i in sorted(EventRecord.objects.filter(asset=asset),
                             key=lambda x: x.motion_data.get("event_date","1970-01-01"), reverse=True)]
    else:
        events = [i for i in sorted(EventRecord.objects.all(),
                             key=lambda x: x.motion_data.get("event_date","1970-01-01"), reverse=True)]

    paginator = Paginator(events, 20)

    context["events"] = paginator.get_page(page)


    html_template = loader.get_template("events/" + page_template)

    try:
        return HttpResponse(html_template.render(context, request))

    except Exception as e:
        if "DEBUG" in os.environ and os.environ["DEBUG"]:
            raise e
        html_template = loader.get_template("site/page-500.html")
        return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def event_collection(request):
    """
    This view generates the event table page. It uses the event-table.html
    """
    context = {}
    page_template = "event-table.html"
    context["segment"] = "event-table.html"

    page = request.GET.get("page", 1)
    try:
        page = int(page)
    except:
        page = 1
    
    asset = request.GET.get("asset", None)

    if asset is not None:
        events = [i for i in reversed(sorted(EventRecord.objects.filter(asset=asset),
                             key=lambda x: x.motion_data.get("event_date","1970-01-01")))]
    else:
        events = [i for i in reversed(sorted(EventRecord.objects.all(),
                             key=lambda x: x.motion_data.get("event_date","1970-01-01")))]
    
    # Paginator for 10 items per page
    paginator = Paginator(events, 15)


# reversed(sorted(Event.objects.all(),
#                                         key=lambda x: x.motion_data["event_date"]))
    context["events"] = paginator.get_page(page)


    html_template = loader.get_template("events/" + page_template)

    try:
        return HttpResponse(html_template.render(context, request))

    except Exception as e:
        if "DEBUG" in os.environ and os.environ["DEBUG"]:
            raise e
        html_template = loader.get_template("site/page-500.html")
        return HttpResponse(html_template.render(context, request))

