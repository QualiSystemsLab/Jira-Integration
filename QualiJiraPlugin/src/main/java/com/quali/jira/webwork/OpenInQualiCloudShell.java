package com.quali.jira.webwork;

import com.quali.jira.Config;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.atlassian.jira.web.action.JiraWebActionSupport;

import java.io.*;
import java.lang.Thread;

import java.net.HttpURLConnection;
import javax.net.ssl.HttpsURLConnection;
import java.net.URL;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.net.ssl.*;
import java.security.cert.*;
import javax.inject.Inject;

import com.atlassian.sal.api.pluginsettings.*;

public class OpenInQualiCloudShell extends JiraWebActionSupport
{
    private static final Logger log = LoggerFactory.getLogger(OpenInQualiCloudShell.class);
    private final Config config;

    private String resid = "NoResid";
    private String resource = "NoResource";
    private String resname = "No reservation created";
    private String csdomain = "NoDomain";
    private String issueid = "NoIssueId";
    private String rawquery = "NoRawQuery";
    private String warnings = "";
    private String originaldomains = "NoOriginalDomains";
    private String clickheremessage = "";
    private String errmsg = "";
    private String debugmsg = "";
    String executionid = "NoExecutionId";
    String workerresid = "NoWorkerReservationId";

    @Inject
    public OpenInQualiCloudShell(PluginSettingsFactory pluginSettingsFactory) {
        super();
        config = new Config(pluginSettingsFactory);
    }

    private String http(String method, String url0, String body, String token) throws Exception {
        URL url = new URL(url0);

        TrustManager[] trustAllCerts = new TrustManager[] { new X509TrustManager() {
            public java.security.cert.X509Certificate[] getAcceptedIssuers() { return null; }
            public void checkClientTrusted(X509Certificate[] certs, String authType) { }
            public void checkServerTrusted(X509Certificate[] certs, String authType) { }

        } };

        SSLContext sc = SSLContext.getInstance("SSL");
        sc.init(null, trustAllCerts, new java.security.SecureRandom());
        HttpsURLConnection.setDefaultSSLSocketFactory(sc.getSocketFactory());

        HostnameVerifier allHostsValid = new HostnameVerifier() {
            public boolean verify(String hostname, SSLSession session) { return true; }
        };
        HttpsURLConnection.setDefaultHostnameVerifier(allHostsValid);

        HttpURLConnection connection = (HttpURLConnection)url.openConnection();
        connection.setRequestMethod(method.toUpperCase());
        connection.setRequestProperty("Content-Length", ""+body.getBytes().length);
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestProperty("Accept", "application/json");
        if(token != null && token.length() > 0)
            connection.setRequestProperty("Authorization", "Basic " + token.trim());
        connection.setUseCaches (false);
        connection.setDoInput(true);
        if(body != null && body.length() > 0) {
            connection.setDoOutput(true);
            DataOutputStream wr = new DataOutputStream(connection.getOutputStream());
            wr.writeBytes(body);
            wr.flush();
            wr.close();
        }
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
                errmsg += "QS_RESOURCE(resource name) not found in issue description. ";
            } else {
                resource = matcher.group(1);
            }
        }
        {
            Pattern pattern = Pattern.compile("QS_DOMAIN[(]([^)]*)[)]");
            Matcher matcher = pattern.matcher(rawquery);
            if(!matcher.find()) {
                errmsg += "QS_DOMAIN(domain name) not found in issue description. ";
            } else {
                csdomain = matcher.group(1);
            }
        }
        {
            Pattern pattern = Pattern.compile("QS_ORIGINAL_DOMAINS[(]([^)]*)[)]");
            Matcher matcher = pattern.matcher(rawquery);
            if(!matcher.find()) {
                errmsg += "QS_ORIGINAL_DOMAINS(domain name) not found in issue description. ";
            } else {
                originaldomains = matcher.group(1);
            }
        }
        {
            Pattern pattern = Pattern.compile("issueid=([^&]*)");
            Matcher matcher = pattern.matcher(rawquery);
            if(!matcher.find()) {
                errmsg += "Issue ID missing from URL";
                issueid = "Issue ID missing from URL";
            } else {
                issueid = matcher.group(1);
            }
        }
        if(errmsg.length() > 0)
            return super.execute();
        resname = resource + " debug session - issue " + issueid;

        String token = "";
        try {
            String url = config.api_url + "/api/login";
            String body = "{  \"username\": \"" + config.csuser + "\",  \"password\": \"" + config.cspass + "\",   \"domain\": \"" + csdomain + "\"}";
            debugmsg += url + "\n" + body + "\n";
            String s = http("PUT", url, body, null);
            debugmsg += s;
            token = s.replaceAll("\"", "");
        } catch(Exception e) {
            errmsg += "Failed to log in to CloudShell sandbox API: " + e.toString();
        }
        if(errmsg.length() > 0)
            return super.execute();

        try {
            String url = config.api_url + "/api/v2/blueprints/JiraSupport/start";
            String body = "{  \"duration\": \"PT5M\",  \"name\": \"jiraworker\"  }";
            debugmsg += url + "\n" + body + "\n";
            String s = http("POST", url, body, token);
            debugmsg += s;
            Pattern pattern = Pattern.compile("\"id\":\"([^\"]*)\"");
            Matcher matcher = pattern.matcher(s);
            if(!matcher.find()) {
                errmsg += "Failed to create reservation: " + s;
                return super.execute();
            }
            workerresid = matcher.group(1);
        } catch(Exception e) {
            errmsg += "Failed to create reservation: " + e.toString();
        }
        if(errmsg.length() > 0)
            return super.execute();
        try {
            String url = config.api_url + "/api/v2/sandboxes/"+workerresid+"/commands/CreateJiraSandbox/start";
            String body = "{ \"params\": [";

            body += "{\"name\":\"reservation_name\",\"value\":\""+resname+"\"}, ";
            body += "{\"name\":\"resource_name\",\"value\":\""+resource+"\"}, ";
            body += "{\"name\":\"duration_in_minutes\",\"value\":\"" + config.sandbox_minutes + "\"}, ";
            body += "{\"name\":\"user\", \"value\":\""+config.csuser+"\"}, ";
            body += "{\"name\":\"jira_url\", \"value\":\""+config.jira_url+"\"}, ";
            body += "{\"name\":\"issue_type\", \"value\":\""+config.issue_type+"\"}, ";
            body += "{\"name\":\"project_name\", \"value\":\""+config.project_name+"\"}, ";
            body += "{\"name\":\"support_domain\", \"value\":\""+config.support_domain+"\"}, ";
            body += "{\"name\":\"jira_username\", \"value\":\""+config.jira_username+"\"}, ";
            body += "{\"name\":\"jira_password\", \"value\":\""+config.jira_password+"\"} ";
            body += "], \"printOutput\": true }";
            debugmsg += url + "\n" + body + "\n";

            String s = http("POST", url, body, token);
            debugmsg += s;
            Pattern pattern = Pattern.compile("/executions/([^\"]*)\"");
            Matcher matcher = pattern.matcher(s);
            if(!matcher.find()) {
                debugmsg += "Failed to get CreateJiraSandbox execution id: " + s;
                return super.execute();
            }
            executionid = matcher.group(1);
        } catch(Exception e) {
            errmsg += "Failed to run CreateJiraSandbox: " + e.toString();
        }

        if(errmsg.length() > 0)
            return super.execute();
        for(int i=0;i<5;i++) {
            try {
                String url = config.api_url + "/api/v2/executions/" + executionid;
                String s = http("GET", url, "", token);
                debugmsg = url + "\n" + s;
                if(s.replaceAll(" ", "").contains("\"status\":\"Completed\"")) {
                    Pattern pattern = Pattern.compile("\"output\":\"([^\"]*)\"");
                    Matcher matcher = pattern.matcher(s);
                    if(!matcher.find()) {
                        debugmsg = "Output not extracted: " + s;
                        return super.execute();
                    }
                    resid = matcher.group(1);
                    resid = resid.replace('\\', ' ').replaceAll(" r n", "");
                    break;
                }
                if(s.replaceAll(" ", "").contains("\"status\":\"Failed\"") || s.replaceAll(" ", "").contains("\"status\":\"Error\"")) {
                    debugmsg = "CreateJiraSandbox failed: " + s;
                    break;
                }
                Thread.sleep(5000);

            } catch (Exception e) {
                errmsg = "CreateJiraSandbox failed: " + e.toString();
            }
        }
        if(errmsg.length() > 0)
            return super.execute();
        try {
            String url = config.api_url + "/api/v2/sandboxes/"+workerresid+"/stop";
            debugmsg = url + "\n";
            String s = http("POST", url, "", token);
            debugmsg += s;
        } catch(Exception e) {
            warnings += "Warning: Failed to stop jiraworker sandbox: " + e.toString();
        }
        clickheremessage = "Click here to open CloudShell sandbox:";
        return super.execute(); //returns SUCCESS
    }
    public String getDebug() { return debugmsg; }
    public String getPortalurl() { return config.portal_url; }
    public String getResid() { return resid; }
    public String getClickHereMessage() { return clickheremessage; }
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
        if (errmsg.length() > 0) {
            return "Error: " + errmsg;
        } else {
            return "";
        }
    }
}
