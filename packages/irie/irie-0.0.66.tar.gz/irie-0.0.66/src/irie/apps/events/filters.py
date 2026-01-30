import django_filters
from django.forms import CheckboxInput

class EventFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        lookup_expr="icontains", 
        field_name="usgsid",
        label="Search"
    )

    max_year = django_filters.NumberFilter(
        label="Max Year",
        method="filter_year"
    )

    def filter_year(self, queryset, name, value):
        ids = {
            asset.id for asset in queryset if (
                asset.nbi_data and int(asset.nbi_data["NBI_BRIDGE"].get("Year Built",0) or 0) <= int(value) #.year
            )
        }
        return queryset.filter(id__in=ids)
 
