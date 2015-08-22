from django import forms
from piebase.models import Project,Organization
from django.template.defaultfilters import slugify


class CreateProjectForm(forms.ModelForm):

	def __init__(self, *args, **kwargs):
		self.organization = kwargs.pop('organization', None)
		super(CreateProjectForm, self).__init__(*args, **kwargs)

	class Meta:
		model = Project
		fields = ['name','description']

	def clean_name(self):
		name = self.cleaned_data['name']
		slug = slugify(name)
		print slug
		if(Project.objects.filter(organization=self.organization, slug=slug)):
			raise forms.ValidationError('Project with this name already exists.')
		return name

