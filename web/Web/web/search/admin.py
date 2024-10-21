from django.contrib import admin

from web.search.models import SearchResult, Query, SERPClick


@admin.register(SearchResult)
class SearchResultAdmin(admin.ModelAdmin):
    list_display = ('username', 'session', 'query', 'SERP', 'page_number', 'num_display')
    list_filter = ('username', 'session', 'query', 'SERP', 'page_number', 'num_display')
    search_fields = ('username', 'session', 'query', 'SERP', 'page_number', 'num_display')

@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ('username', 'session', 'query', 'query_id', 'created_at', 'updated_at')
    list_filter = ('username', 'session', 'query', )
    search_fields = ('username', 'session', 'query', 'query_id')

@admin.register(SERPClick)
class SERPClickAdmin(admin.ModelAdmin):
    list_display = ('username', 'session', 'docno', 'created_at', 'updated_at')
    list_filter = ('username', 'session', 'docno', 'created_at', 'updated_at')
    search_fields = ('username', 'session', 'docno', 'created_at', 'updated_at')
