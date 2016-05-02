// Util to handle project, node and parent properties
function ProjectUtils() {}

ProjectUtils.getProjectData = function() {
	var projectData = document.getElementsByTagName('body')[0];
	var nodeId = projectData.getAttribute('data-node_id');
	var parentNodeId = projectData.getAttribute('data-parent_node_id');
	var projectId = projectData.getAttribute('data-project_id');
	var isProject = projectData.getAttribute('data-is_project');
	var nodeType = projectData.getAttribute('data-node_type');
	return {
		nodeId: nodeId,
		parentNodeId: parentNodeId,
		projectId: projectId,
		isProject: isProject,
		nodeType: nodeType}
};

ProjectUtils.nodeId = function() {
	return ProjectUtils.getProjectData().nodeId;
}

ProjectUtils.parentNodeId = function() {
	return ProjectUtils.getProjectData().parentNodeId;
}

ProjectUtils.projectId = function() {
	return ProjectUtils.getProjectData().projectId;
}

ProjectUtils.isProject = function() {
	return ProjectUtils.getProjectData().isProject;
}

ProjectUtils.nodeType = function() {
	return ProjectUtils.getProjectData().nodeType;
}

ProjectUtils.setProjectAttributes = function(props) {
	var projectData = document.getElementsByTagName('body')[0];
	for (var key in props) {
		if (props.hasOwnProperty(key)) {
			keyAttr = 'data-' + key.replace(/([A-Z])/g, function($1){return "_"+$1.toLowerCase();});
			projectData.setAttribute(keyAttr, props[key]);
		}
	}
}



