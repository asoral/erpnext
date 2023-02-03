Dear Customer<h5>{{ doc.customer }},</h5>

<p><p>This is a follow-up email for Ticket/Issue <h5>{{ doc.subject }}</h5> .The current status of issue in our ERP is Customer Verification Pending i.e. pending from your end. Testing is done from our end and solution is written under Resolution Details section. Please verify from your end and do reply to this mail as "Closed the Issue" OR If something is pending related to this Ticket/Issue from Dexciss side, please do reply as "Pending" We will fix it and again connect with you.


<p><p><h5>Please go through the following details:</h5>


<p>Project ID: {{ doc.project }}
<p>Project Name : {{ doc.project_name }}
<p>Issue ID : {{ doc.name }}
<p>Issue Name : {{ doc.subject }}


<p><p>
<h5>Description :</h5>
<p>{{ doc.description }}


<p><p>
<h5>Resolution Details:</h5>
<p>{{ doc.resolution_details }}


<p><p><p>If you have any concerns please connect with us through notifications@dexciss.com</h5>

<p>Regards,
<p>Team Implementation,
<p>Dexciss Technology Pvt.Ltd.