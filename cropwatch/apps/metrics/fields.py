import sys

from django.forms.models import modelform_factory
from inplaceeditform.fields import BaseAdaptorField

from cropwatch.apps.metrics.forms import HabitatManageForm

if sys.version_info[0] == 2:
    string = basestring
else:
    string = str
unicode = str


class MyAdaptor(BaseAdaptorField):
    MULTIPLIER_HEIGHT = 1.75
    INCREASE_WIDTH = 40

    @property
    def name(self):
        return 'myadaptor'

    def treatment_height(self, height, font_size, width=None):
        if 'height' in self.config:
            effective_height = height
        else:
            effective_height = font_size
        return "%spx" % (effective_height * self.MULTIPLIER_HEIGHT)

    def treatment_width(self, width, font_size, height=None):
        return "%spx" % (width + self.INCREASE_WIDTH)

    def render_value(self, field_name=None):
        value = super(MyAdaptor, self).render_value(field_name)
        if not isinstance(value, string):
            value = unicode(value)
        return value

    def get_form_class(self):
        # The form has to be here, 
        return modelform_factory(self.model, form=HabitatManageForm, fields='__all__')

    # and request.user has to be injected here, 
    def get_form(self):
        form_class = self.get_form_class()
        return form_class(instance=self.obj, initial=self.initial, prefix=id(form_class), user=self.request.user, )

    def get_value_editor(self, value):
        value = super(MyAdaptor, self).get_value_editor(value)
        return value and value.pk

    def save(self, value):
        setattr(self.obj, "%s_id" % self.field_name, value)
        self.obj.save()



if sys.version_info[0] == 2:
    string = basestring
else:
    string = str
unicode = str


class ScheduleChange(BaseAdaptorField):
    MULTIPLIER_HEIGHT = 1.75
    INCREASE_WIDTH = 40

    @property
    def name(self):
        return 'schedule_change'

    def treatment_height(self, height, font_size, width=None):
        if 'height' in self.config:
            effective_height = height
        else:
            effective_height = font_size
        return "%spx" % (effective_height * self.MULTIPLIER_HEIGHT)

    def treatment_width(self, width, font_size, height=None):
        return "%spx" % (width + self.INCREASE_WIDTH)

    def render_value(self, field_name=None):
        value = super(ScheduleChange, self).render_value(field_name)
        if not isinstance(value, string):
            value = unicode(value)
        return value

    #	def get_form_class(self):
    # The form has to be here,
    #		return modelform_factory(self.model, form=HabitatManageForm, fields='__all__')

    # and request.user has to be injected here,
    #	def get_form(self):
    #		form_class = self.get_form_class()
    #		return form_class(instance=self.obj, initial=self.initial, prefix=id(form_class), user=self.request.user, )

    #	def get_value_editor(self, value):
    #		value = super(ScheduleChange, self).get_value_editor(value)
    #		return value and value.pk

    def save(self, value):
        self.obj.end = self.obj.start
        setattr(self.obj, "%s_id" % self.field_name, value)

        self.obj.save()
