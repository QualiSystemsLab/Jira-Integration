package com.quali.jira.webwork;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.atlassian.jira.web.action.JiraWebActionSupport;

import java.io.*;

import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Properties;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class OpenInQualiCloudShell extends JiraWebActionSupport
{
    private static final Logger log = LoggerFactory.getLogger(OpenInQualiCloudShell.class);

    private String resid = "NoResid";
    private String qsoutput = "QSNoOutput";
    private String resource = "NoResource";
    private String resname = "NoReservationName";
    private String csdomain = "NoDomain";
    private String issueid = "NoIssueId";
    private int duration = 120;
    private String rawquery = "NoRawQuery";
    private String warnings = "";

    private String apiip;
    private String portalip;
    private String apihttphttps;
    private String portalhttphttps;
    private String apiport;
    private String portalport;
    private String csuser;
    private String cspass;

    public OpenInQualiCloudShell() {
        super();
        String f1 = "c:\\ProgramData\\QualiSystems\\QualiJiraPlugin.properties";
        String f2 = "/var/lib/quali/QualiJiraPlugin.properties";
        Properties prop = new Properties();
        InputStream input;
        try {
            try {
                input = new FileInputStream(f1);
            } catch(Exception e1) {
                input = new FileInputStream(f2);
            }
            prop.load(input);
        } catch (IOException ex) {
            warnings += "Failed to load " + f1 + " and " + f2 + ". Using CloudShell portal http://localhost:80 and API http://localhost:8029 admin/admin. Settings supported in QualiJiraPlugin.properties: api_host, portal_host, api_http_or_https, portal_http_or_https, api_port, portal_port, cloudshell_username, cloudshell_password";
            prop = new Properties();
        }
        apiip = prop.getProperty("api_host", "localhost");
        portalip = prop.getProperty("portal_host", "localhost");
        apihttphttps = prop.getProperty("api_http_or_https", "http");
        portalhttphttps = prop.getProperty("portal_http_or_https", "http");
        apiport = prop.getProperty("api_port", "8029");
        portalport = prop.getProperty("portal_port", "80");
        csuser = prop.getProperty("cloudshell_username", "admin");
        cspass = prop.getProperty("cloudshell_password", "admin");
    }

    private String http(String url0, String body, String token) throws Exception {
        URL url = new URL(url0);
        HttpURLConnection connection = (HttpURLConnection)url.openConnection();
        connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Length", ""+body.getBytes().length);
        connection.setRequestProperty("Authorization", "MachineName="+apiip+";Token=" + token);
        connection.setRequestProperty("Host", apiip+":"+apiport);
        connection.setRequestProperty("Accept", "*/*");
        connection.setRequestProperty("Content-Type", "text/xml");
        connection.setRequestProperty("DateTimeFormat", "MM/dd/yyyy HH:mm");
        connection.setRequestProperty("ClientTimeZoneId", "UTC");
        connection.setUseCaches (false);
        connection.setDoInput(true);
        connection.setDoOutput(true);
        DataOutputStream wr = new DataOutputStream(connection.getOutputStream());
        wr.writeBytes(body);
        wr.flush();
        wr.close();
        InputStream is = connection.getInputStream();
        BufferedReader rd = new BufferedReader(new InputStreamReader(is));
        StringBuilder response = new StringBuilder();
        for(;;) {
            String line = rd.readLine();
            if(line==null)
                break;
            response.append(line);
            response.append('\n');
        }
        rd.close();
        connection.disconnect();
        return response.toString();
    }

    @Override
    public String execute() throws Exception {
        rawquery = java.net.URLDecoder.decode(getHttpRequest().getQueryString(), "UTF-8");
        {
            Pattern pattern = Pattern.compile("QS_RESOURCE[(]([^)]*)[)]");
            Matcher matcher = pattern.matcher(rawquery);
            if(!matcher.find()) {
                qsoutput = "QS_RESOURCE(resource name) not found in issue description";
                return super.execute();
            }
            resource = matcher.group(1);
        }
        {
            Pattern pattern = Pattern.compile("QS_DOMAIN[(]([^)]*)[)]");
            Matcher matcher = pattern.matcher(rawquery);
            if(!matcher.find()) {
                qsoutput = "QS_DOMAIN(domain name) not found in issue description";
                return super.execute();
            }
            csdomain = matcher.group(1);
        }
        {
            Pattern pattern = Pattern.compile("issueid=([^&]*)");
            Matcher matcher = pattern.matcher(rawquery);
            if(!matcher.find()) {
                issueid = "Issue ID missing from URL";
                return super.execute();
            }
            issueid = matcher.group(1);
        }
        resname = resource + " debug session - issue " + issueid;

        String token = "";
        {
            String s = http(apihttphttps+"://"+apiip+":"+apiport+"/ResourceManagerApiService/Logon",
                    "<Logon>" +
                            "<username>"+csuser+"</username>" +
                            "<password>"+cspass+"</password>" +
                            "<domainName>"+csdomain+"</domainName>" +
                            "</Logon>",
                    "");
            Pattern pattern = Pattern.compile("Token=\"([^\"]*)\"");
            Matcher matcher = pattern.matcher(s);
            if(!matcher.find()) {
                qsoutput = "CloudShell API login failed: " + s;
                return super.execute();
            }
            token = matcher.group(1);
        }


        {
            String s = http(apihttphttps+"://"+apiip+":"+apiport+"/ResourceManagerApiService/CreateImmediateReservation",
                    "<CreateImmediateReservation>\n" +
                            "<reservationName>" + resname + "</reservationName>\n" +
                            "<owner>"+csuser+"</owner>\n" +
                            "<durationInMinutes>" + duration + "</durationInMinutes>\n" +
                            "<notifyOnStart>0</notifyOnStart>\n" +
                            "<notifyOnEnd>0</notifyOnEnd>\n" +
                            "<notificationMinutesBeforeEnd>0</notificationMinutesBeforeEnd>\n" +
                            "<topologyFullPath/>\n" +
                            "<globalInputs/>\n" +
                            "<requirementsInputs/>\n" +
                            "<additionalInfoInputs/>\n" +
                            "</CreateImmediateReservation>",
                    token);
            Pattern pattern = Pattern.compile("Id=\"([^\"]*)\"");
            Matcher matcher = pattern.matcher(s);
            if(!matcher.find()) {
                qsoutput = "Failed to create reservation: " + s;
                return super.execute();
            }
            resid = matcher.group(1);
        }
        {
            String s = http(apihttphttps+"://"+apiip+":"+apiport+"/ResourceManagerApiService/AddResourcesToReservation",
                    "<AddResourcesToReservation>\n" +
                            "<reservationId>" + resid + "</reservationId>\n" +
                            "<resourcesFullPath>\n" +
                            "<string>" + resource + "</string>\n" +
                            "</resourcesFullPath>\n" +
                            "<shared>1</shared>\n" +
                            "</AddResourcesToReservation>",
                    token);
            qsoutput = s;
        }
        {
            String s = http(apihttphttps+"://"+apiip+":"+apiport+"/ResourceManagerApiService/AddServiceToReservation",
                    "  <AddServiceToReservation>\n" +
                            "<reservationId>" + resid + "</reservationId>\n" +
                            "<serviceName>Jira Service</serviceName>\n" +
                            "<alias>Jira Service</alias>\n" +
                            "<attributes></attributes>" +
                            "\n" +
                            "</AddServiceToReservation>",
                    token);
            qsoutput = s;
        }

        return super.execute(); //returns SUCCESS
    }
    public String getQSOutput() {
        return qsoutput;
    }
    public String getPortalhttphttps() {
        return portalhttphttps;
    }
    public String getPortalport() {
        return portalport;
    }
    public String getPortalip() {
        return portalip;
    }
    public String getResid() {
        return resid;
    }
    public String getResname() {
        return resname;
    }
    public String getResource() {
        return resource;
    }
    public String getRawquery() {
        return rawquery;
    }
    public String getWarning() {
        return warnings;
    }
    public String getError() {
        if(resid.equals("NoResId"))
            return "FAILED TO CREATE RESERVATION";
        return "";
    }
}
