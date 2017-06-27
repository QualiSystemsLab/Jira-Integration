package com.quali.jira.webwork;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.atlassian.jira.web.action.JiraWebActionSupport;

import java.net.URLEncoder;
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
    private String bpname = "NoBlueprintName";

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
            warnings += "Failed to load " + f1 + " and " + f2 + ". Using CloudShell portal http://localhost:80 and sandbox API http://localhost:9000 admin/admin. Settings supported in QualiJiraPlugin.properties: api_host, portal_host, api_http_or_https, portal_http_or_https, api_port, portal_port, cloudshell_username, cloudshell_password";
            prop = new Properties();
        }
        apiip = prop.getProperty("api_host", "localhost");
        portalip = prop.getProperty("portal_host", "localhost");
        apihttphttps = prop.getProperty("api_http_or_https", "http");
        portalhttphttps = prop.getProperty("portal_http_or_https", "http");
        apiport = prop.getProperty("api_port", "82");
        portalport = prop.getProperty("portal_port", "80");
        csuser = prop.getProperty("cloudshell_username", "admin");
        cspass = prop.getProperty("cloudshell_password", "admin");
    }

    private String http(String method, String url0, String body, String token) throws Exception {
        URL url = new URL(url0);
        HttpURLConnection connection = (HttpURLConnection)url.openConnection();
        connection.setRequestMethod(method.toUpperCase());
        connection.setRequestProperty("Content-Length", ""+body.getBytes().length);
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestProperty("Accept", "application/json");
        if(token != null && token.length() > 0)
            connection.setRequestProperty("Authorization", "Basic " + token.trim());
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
            Pattern pattern = Pattern.compile("QS_BLUEPRINT_NAME[(]([^)]*)[)]");
            Matcher matcher = pattern.matcher(rawquery);
            if(!matcher.find()) {
                qsoutput = "QS_BLUEPRINT_NAME(blueprint name) not found in issue description";
                return super.execute();
            }
            bpname = matcher.group(1);
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
            String s = http("PUT", apihttphttps + "://" + apiip + ":" + apiport + "/api/login",
                    "{  \"username\": \"" + csuser + "\",  \"password\": \""+cspass+"\",   \"domain\": \""+csdomain+"\"}",
                    token);

            token = s.replaceAll("\"", "");
        }

        try {
            String url = apihttphttps + "://" + apiip + ":" + apiport + "/api/v2/blueprints/" +
//                    URLEncoder.encode(bpname, "UTF-8").replaceAll("[+]", "%20")
                    bpname.replaceAll(" ", "%20")
                    + "/start";
            String body = "{  \"duration\": \"PT23H\",  \"name\": \"" + resname + "\"  }";
            String s = http("POST", url, body, token);
            qsoutput = url + "\n" + body + "\n" + s;
            Pattern pattern = Pattern.compile("\"id\":\"([^\"]*)\"");
            Matcher matcher = pattern.matcher(s);
            if(!matcher.find()) {
                qsoutput = "Failed to create reservation: " + s;
                return super.execute();
            }
            resid = matcher.group(1);
        } catch(Exception e) {
            qsoutput = "Failed to create reservation: " + e.toString();
            return super.execute();
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
